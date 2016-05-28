# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from types import NoneType
from collections import namedtuple, Iterable

from .dsl_supported_versions import (
    VersionNumber, VersionStructure, add_version_to_database)
from .framework.functions import register, unregister, Function
from .framework import Element

__all__ = [
    'VersionNumber',
    'VersionStructure',
    'add_version_to_database',
    'IntrinsicFunctionExtension',
    'ElementExtension',
    'ParserExtender',
    'Element',
    'Function',
]

_BaseFunctionExtension = namedtuple(
    'IntrinsicFunctionExtension', 'action, name, function')
_BaseElementExtension = namedtuple(
    'ElementExtension', 'action, target_element, new_element, schema_key')


class _ValidatorMixin(object):
    _ACTION_EXTENSION_MESSAGE = 'action arg options: {actions}, got {action}'
    _ARGUMENT_TYPE_EXTENSION_MESSAGE = (
        '{name} argument mast be {type} based, got {arg!r}')

    @classmethod
    def validate_actions(cls, action):
        if action not in cls.ACTIONS:
            raise TypeError(cls._ACTION_EXTENSION_MESSAGE.format(
                actions=cls.ACTIONS, action=action))

    @classmethod
    def validate_type(cls, argument_name, argument, expected_type):
        if not issubclass(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXTENSION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_instance(cls, argument_name, argument, expected_type):
        if not isinstance(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_EXTENSION_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))


class IntrinsicFunctionExtension(_BaseFunctionExtension, _ValidatorMixin):
    # todo: maybe add replace action and check in add that we don't replace...
    ADD_FUNCTION_ACTION = 'add'
    REMOVE_FUNCTION_ACTION = 'remove'
    ACTIONS = (ADD_FUNCTION_ACTION, REMOVE_FUNCTION_ACTION)

    def __new__(cls, action, name, function):
        cls.validate_actions(action)
        cls.validate_type('function', function, Function)
        cls.validate_instance('name', name, basestring)
        return super(IntrinsicFunctionExtension, cls).__new__(
            cls, action, name, function)


class ElementExtension(_BaseElementExtension, _ValidatorMixin):
    REPLACE_ELEMENT_ACTION = 'replace'
    ADD_ELEMENT_TO_SCHEMA_ACTION = 'schema'
    CHANGE_ELEMENT_VERSION = 'supported_version'
    ACTIONS = (
        REPLACE_ELEMENT_ACTION,
        ADD_ELEMENT_TO_SCHEMA_ACTION,
        CHANGE_ELEMENT_VERSION,
    )

    def __new__(
            cls,
            action,
            target_element,
            new_element=None,
            schema_key=None):
        cls.validate_actions(action)

        cls.validate_type('target_element', target_element, Element)
        if action != cls.CHANGE_ELEMENT_VERSION:
            cls.validate_type('new_element', new_element, Element)
        else:
            cls.validate_instance('new_element', new_element, NoneType)

        cls.validate_instance(
            'schema_key', schema_key,
            basestring
            if action == cls.ADD_ELEMENT_TO_SCHEMA_ACTION else
            NoneType)

        return super(ElementExtension, cls).__new__(
            cls, action, target_element, new_element, schema_key)


class ParserExtender(_ValidatorMixin):
    def __init__(self):
        self._intrinsic_function_handlers = {
            IntrinsicFunctionExtension.ADD_FUNCTION_ACTION:
                self._add_function,
            IntrinsicFunctionExtension.REMOVE_FUNCTION_ACTION:
                self._remove_function,
        }
        self._element_handlers = {
            ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION:
                self._add_to_schema,
            ElementExtension.REPLACE_ELEMENT_ACTION:
                self._replace_element,
            ElementExtension.CHANGE_ELEMENT_VERSION:
                self._change_element_version
        }

    def extend(
            self,
            version_structure,
            element_extensions=(),
            function_extensions=()):
        """

        :param version_structure
        :type version_structure: VersionStructure
        :param element_extensions:
        :type element_extensions: (tuple, list)
        :param function_extensions:
        :type function_extensions: (tuple, list)
        """
        self.validate_instance(
            'version_structure', version_structure, (VersionStructure, None))
        self.validate_instance(
            'element_expansions', element_extensions, Iterable)
        self.validate_instance(
            'function_expansions', function_extensions, Iterable)

        self.extend_elements(
            element_extensions, version_structure=version_structure)
        self.extend_intrinsic_functions(
            function_extensions, version_structure=version_structure)

    def extend_elements(self, extensions, version_structure):
        for extension in extensions:
            self._run_handler(
                extension,
                handlers=self._element_handlers,
                version_structure=version_structure,
                type_check=ElementExtension)

    def extend_intrinsic_functions(self, extensions, version_structure):
        for extension in extensions:
            self._run_handler(
                extension,
                handlers=self._intrinsic_function_handlers,
                version_structure=version_structure,
                type_check=IntrinsicFunctionExtension)

    def _run_handler(self, extension, handlers, version_structure, type_check):
        self.validate_instance(
            extension.__class__.__name__,
            extension,
            type_check)
        handlers[extension.action](extension, version_structure)

    def _add_version_to_support(self, element, version_structure):
        add_version_to_database(version_structure.profile, version_structure)
        element.supported_version = version_structure

    def _remove_function(self, expansion, version_structure):
        unregister(name=expansion.name)

    def _add_function(self, expansion, version_structure):
        self._add_version_to_support(expansion.function, version_structure)
        register(expansion.function, name=expansion.name)

    def _add_to_schema(self, expansion, version_structure):
        self._add_version_to_support(expansion.new_element, version_structure)
        expansion.target_element.schema[
            expansion.schema_key] = expansion.new_element

    def _replace_element(self, expansion, version_structure):
        element_name = expansion.target_element.__name__
        base_package = __package__.split('.')[0]
        for module in sys.modules.itervalues():
            if not module or not module.__name__.startswith(base_package):
                continue
            try:
                element = getattr(module, element_name)
                if all([issubclass(element, Element),
                        element.extend is not expansion.new_element]):
                    self._add_version_to_support(element, version_structure)
                    self._add_version_to_support(
                        expansion.new_element, version_structure)
                    element.extend = expansion.new_element
            except AttributeError:
                pass

    def _change_element_version(self, expansion, version_structure):
        self._add_version_to_support(
            expansion.target_element, version_structure)

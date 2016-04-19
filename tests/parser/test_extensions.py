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

from aria.parser.framework.functions import template_functions
from aria.parser.framework.elements.blueprint import Blueprint
from aria.parser.extension_tools import (
    Element,
    ElementExtension,
    Function,
    IntrinsicFunctionExtension,
)
from aria.parser import extend
from .suite import ParserTestCase, TestCase


class _TestBlueprint(Blueprint):
    called = []

    def parse(self, **kwargs):
        self.called.append(1)
        return super(_TestBlueprint, self).parse(**kwargs)


class _TestElement(Element):
    called = []
    schema = {}

    def parse(self, **kwargs):
        self.called.append(1)
        return super(_TestElement, self).parse(**kwargs)


class _GetTrueFunction(Function):
    called = []

    def evaluate(self, plan):
        self.called.append(1)
        return True

    def parse_args(self, args):
        self.called.append(1)

    def validate(self, plan):
        self.called.append(1)

    def evaluate_runtime(self, storage):
        self.called.append(1)


class TestExtensions(ParserTestCase):
    def test_replace_element_extension(self):
        blueprint_extension = ElementExtension(
            action=ElementExtension.REPLACE_ELEMENT_ACTION,
            target_element=Blueprint,
            new_element=_TestBlueprint)
        extend(element_extensions=[blueprint_extension])

        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.parse()
        self.assertTrue(bool(_TestBlueprint.called))

    def test_add_to_schema_element_extension(self):
        blueprint_extension = ElementExtension(
            action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
            target_element=Blueprint,
            new_element=_TestElement,
            schema_key='test')
        extend(element_extensions=[blueprint_extension])

        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
test: {}
"""
        self.parse()
        self.assertTrue(bool(_TestElement.called))

    def test_add_function_extension(self):
        get_true_function_extension = IntrinsicFunctionExtension(
            action=IntrinsicFunctionExtension.ADD_FUNCTION_ACTION,
            name='get_true',
            function=_GetTrueFunction)
        extend(function_extensions=[get_true_function_extension])

        self.template.version_section('1.0')
        self.template.node_type_section(
            default='{ get_true: [] }'
        )
        self.template += (
            '\nnode_templates:\n'
            '    test_node:\n'
            '        type: test_type\n'
        )
        self.parse()
        self.assertTrue(_GetTrueFunction.called)
        self.assertIn('get_true', template_functions.keys())
        self.assertIn(_GetTrueFunction, template_functions.values())

    def test_remove_function_extension(self):
        self.test_add_function_extension()
        get_true_function_extension = IntrinsicFunctionExtension(
            action=IntrinsicFunctionExtension.REMOVE_FUNCTION_ACTION,
            name='get_true',
            function=_GetTrueFunction)
        extend(function_extensions=[get_true_function_extension])
        self.assertTrue('get_true' not in template_functions.keys())
        self.assertTrue(_GetTrueFunction not in template_functions.values())


class TestExtensionValidation(TestCase):
    def test_element_validation(self):
        self.assertRaises(
            excClass=TypeError,
            callableObj=ElementExtension,
            action='action',
            target_element=_TestBlueprint,
            new_element=_TestElement,
            schema_key=None,
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=ElementExtension,
            action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
            target_element=_TestBlueprint,
            new_element=_TestElement,
            schema_key=10,
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=ElementExtension,
            action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
            target_element=object,
            new_element=_TestElement,
            schema_key='key',
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=ElementExtension,
            action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
            target_element=_TestBlueprint,
            new_element=object,
            schema_key='key',
        )

    def test_function_validation(self):
        self.assertRaises(
            excClass=TypeError,
            callableObj=IntrinsicFunctionExtension,
            action='action',
            function=_GetTrueFunction,
            name='key',
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=IntrinsicFunctionExtension,
            action=IntrinsicFunctionExtension.ADD_FUNCTION_ACTION,
            function=_GetTrueFunction,
            name=None,
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=IntrinsicFunctionExtension,
            action=IntrinsicFunctionExtension.ADD_FUNCTION_ACTION,
            function=object,
            name='key',
        )

    def test_extend_method_validation(self):
        self.assertRaises(
            excClass=TypeError,
            callableObj=extend,
            element_extensions=dict(),
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=extend,
            function_extensions=dict()
        )

        self.assertRaises(
            excClass=TypeError,
            callableObj=extend,
            extensions=None
        )

        self.assertRaises(TypeError, extend, None)

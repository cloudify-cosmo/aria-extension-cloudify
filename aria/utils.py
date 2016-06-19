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

import os
from importlib import import_module


def plugin_installer(path, plugin_suffix, package=None, callback=None):
    """

    :param path:
    :param plugin_suffix:
    :param package:
    :param callback:
    :return:
    """
    assert callback is None or callable(callback)
    plugin_suffix = '{0}.py'.format(plugin_suffix)

    for file_name in os.listdir(path):
        if not file_name.endswith(plugin_suffix):
            continue
        module_name = '{0}.{1}'.format(package, file_name[:-3]) if package else file_name[:-3]
        module = import_module(module_name)
        if callback:
            callback(module)


class ValidatorMixin(object):
    _ARGUMENT_TYPE_MESSAGE = '{name} argument must be {type} based, got {arg!r}'
    _ACTION_MESSAGE = 'action arg options: {actions}, got {action}'
    _ARGUMENT_CHOICE_MESSAGE = '{name} argument must be in {choices}, got {arg!r}'

    @classmethod
    def validate_actions(cls, action):
        # todo: remove this and use validate choice
        if action not in cls.ACTIONS:
            raise TypeError(cls._ACTION_MESSAGE.format(
                actions=cls.ACTIONS, action=action))

    @classmethod
    def validate_in_choice(cls, name, argument, choices):
        if argument not in choices:
            raise TypeError(cls._ARGUMENT_CHOICE_MESSAGE.format(
                name=name, choices=choices, arg=argument))

    @classmethod
    def validate_type(cls, argument_name, argument, expected_type):
        if not issubclass(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_instance(cls, argument_name, argument, expected_type):
        if not isinstance(argument, expected_type):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type=expected_type, arg=argument))

    @classmethod
    def validate_callable(cls, argument_name, argument):
        if not callable(argument):
            raise TypeError(cls._ARGUMENT_TYPE_MESSAGE.format(
                name=argument_name, type='callable', arg=argument))

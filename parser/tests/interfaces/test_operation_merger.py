#
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import testtools

from cloudify.framework.abstract_test_parser import AbstractTestParser
from aria.presentation.null import NULL, null_to_none

# from . import validate


def raw_operation_mapping(implementation=None,
                          inputs=None,
                          executor=None,
                          max_retries=None,
                          retry_interval=None):

    """
    Used to simulate a possible operation written in
    the blueprint.
    """

    inputs = inputs or {}
    result = dict(operation=implementation,
                  inputs=inputs,
                  executor=executor,
                  max_retries=max_retries,
                  retry_interval=retry_interval)
    return result


def _create_simple_operation(implementation=None, **_):
    operation = (
        'create: {0}\n'.format(implementation or "{}")
    )
    return operation


def _create_operation_mapping(implementation=None,
                              inputs=None,
                              executor=None,
                              max_retries=None,
                              retry_interval=None):

    operation = (
        'create:\n'
    )

    if implementation:
        operation += '          implementation: {0}\n'.format(implementation)
    if executor:
        operation += '          executor: {0}\n'.format(executor)
    if max_retries is not None:
        operation += '          max_retries: {0}\n'.format(max_retries)
    if retry_interval is not None:
        operation += '          retry_interval: {0}\n'.format(retry_interval)
    if inputs:
        operation += '          inputs:\n'
        for inpt in inputs.keys():
            if type(inputs[inpt]) is dict:
                operation += '            {0}:\n'.format(inpt)
                for prop in inputs[inpt]:
                    operation += '              {0}: {1}\n'.format(prop, inputs[inpt][prop])
            else:
                operation += '            {0}: {1}\n'.format(inpt, inputs[inpt])
    return operation


def create_operation_in_node_type(implementation=None,
                                  inputs=None,
                                  executor=None,
                                  max_retries=None,
                                  retry_interval=None,
                                  operation_mapping=True):

    operation_creation_method = \
        _create_operation_mapping if operation_mapping else _create_simple_operation

    result = (
        '\n'
        'node_types:\n'
        '  test_type:\n'
        '    interfaces:\n'
        '      test_interface1:\n'
        '        {0}\n'.format(operation_creation_method(
            implementation=implementation,
            inputs=inputs,
            executor=executor,
            max_retries=max_retries,
            retry_interval=retry_interval
        ))
    )
    return result


def create_operation_in_node_template(implementation='',
                                      inputs=None,
                                      executor='',
                                      max_retries=None,
                                      retry_interval=None,
                                      operation_mapping=True):

    operation_creation_method = \
        _create_operation_mapping if operation_mapping else _create_simple_operation

    result = (
        '\n'
        'node_templates:\n'
        '  test_node:\n'
        '    type: test_type\n'
        '    interfaces:\n'
        '      test_interface1:\n'
        '        {0}\n'.format(operation_creation_method(
            implementation=implementation,
            inputs=inputs,
            executor=executor,
            max_retries=max_retries,
            retry_interval=retry_interval
        ))
    )
    return result

NO_OP = raw_operation_mapping()
TYPE_WITH_NONE_OP = (
    '\n'
    'node_types:\n'
    '  test_type:\n'
    '    interfaces:\n'
    '      test_interface1:\n'
    '        create:\n'
)
TEMPLATE_WITH_NONE_OP = (
    '\n'
    'node_templates:\n'
    '  test_node:\n'
    '    type: test_type\n'
    '    interfaces:\n'
    '      test_interface1:\n'
    '        create:\n'
)


class NodeTemplateNodeTypeOperationMergerTest(AbstractTestParser):

    def _assert_operations(self,
                           yaml,
                           expected_operation,
                           dsl_version=AbstractTestParser.BASIC_VERSION_SECTION_DSL_1_0):
        plan = self.parse(yaml, dsl_version=dsl_version)
        actual_operation = plan['nodes'][0]['operations']['create']
        if expected_operation is None:
            self.assertIsNone(actual_operation)
        else:
            for prop in expected_operation.keys():
                if actual_operation[prop] == NULL:
                    actual_operation[prop] = null_to_none(actual_operation[prop])
                if prop == 'operation' and actual_operation[prop]:
                    self.assertEqual(expected_operation[prop],
                                     actual_operation['plugin'] + '.' + actual_operation[prop])
                else:
                    self.assertEqual(expected_operation[prop], actual_operation[prop])

    def create_dsl_blueprint(self,
                             node_type1_operation,
                             node_template1_operation,
                             node_type2_operation=None,
                             add_plugin=True):

        plugin = self.BASIC_PLUGIN if add_plugin else ''

        dsl_blueprint = """
tosca_definitions_version: cloudify_dsl_1_3
node_types:
    cloudify.nodes.Compute: {{}}
    type1:
        derived_from: cloudify.nodes.Compute
        {node_type1_operation}
    type2:
        derived_from: type1
        {node_type2_operation}
node_templates:
    node1:
        type: type1
        {node_template1_operation}
    node2:
        type: type2
{plugin}
""".format(node_type1_operation=self.create_dsl_operation(node_type1_operation),
           node_type2_operation=self.create_dsl_operation(node_type2_operation),
           node_template1_operation=self.create_dsl_operation(node_template1_operation),
           plugin=plugin)

        return dsl_blueprint

    @staticmethod
    def create_dsl_operation(operation):

        if operation is None:
            return ''

        dsl_operation = """interfaces:
            interface1:
                op1:"""
        if operation == '':
            return '{operation} {{}}'.format(
                operation=dsl_operation
            )
        for line in operation.splitlines():
            dsl_operation += '\n{indentation}{operation_attribute}'.format(
                indentation=20*' ',
                operation_attribute=line)
        return dsl_operation

    @staticmethod
    def create_parsed_operation(operation):
        return {
            'operation': operation.get('operation') or None,
            'plugin': operation.get('plugin') or None,
            'inputs': operation.get('inputs') or {},
            'executor': operation.get('executor') or None,
            'max_retries': operation.get('max_retries'),
            'retry_interval': operation.get('retry_interval'),
            'has_intrinsic_functions': False
        }

    def assert_operation_merger(self,
                                dsl_blueprint,
                                expected_template_merger,
                                expected_type_merger=None):
        parsed_blueprint = self.parse(dsl_blueprint)

        actual_template_merger = parsed_blueprint['nodes'][0]['operations'].get('op1', None)
        self.assertEqual(expected_template_merger, actual_template_merger)

        if expected_type_merger:
            actual_type_merger = parsed_blueprint['nodes'][1]['operations'].get('op1', None)
            self.assertEqual(expected_type_merger, actual_type_merger)

    def test_no_op_overrides_no_op(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='',
            node_type2_operation='',
            add_plugin=False)
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})

        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation_mapping_no_inputs(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n',
            node_template1_operation='',
            node_type2_operation='')
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation_mapping(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs: {}',
            node_template1_operation='',
            node_type2_operation='')
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_none(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='',
            node_type2_operation=''
        )
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='',
            node_type2_operation=''
        )
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_no_op_overrides_operation_mapping_with_executor(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='',
            node_type2_operation=''
        )
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_no_op(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='implementation: test_plugin.tasks.create',
            node_type2_operation='implementation: test_plugin.tasks.create',
        )

        expected_template_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_operation_mapping(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs:\n    key:\n        default: value',
            node_template1_operation='test_plugin.tasks.override_create',
            node_type2_operation='test_plugin.tasks.override_create'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_operation_mapping_no_inputs(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create',
            node_template1_operation='test_plugin.tasks.override_create',
            node_type2_operation='test_plugin.tasks.override_create'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_none(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='test_plugin.tasks.create',
            node_type2_operation='test_plugin.tasks.create'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_operation_mapping_with_executor(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='test_plugin.tasks.override_create',
            node_type2_operation='test_plugin.tasks.override_create'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_overrides_operation(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='test_plugin.tasks.override_create',
            node_type2_operation='test_plugin.tasks.override_create'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_no_op(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='implementation: test_plugin.tasks.create\n'
                                     'inputs:\n    key: value',
            node_type2_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs:\n    key:\n        default: value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_operation_mapping(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs:\n    key:\n        default: value',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'inputs:\n    key: override_value',
            node_type2_operation='implementation: test_plugin.tasks.override\n'
                                 'inputs:\n    key:\n        default: override_value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'override_value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'override_value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_operation_mapping_no_inputs(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'inputs:\n    key: value',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'inputs:\n    key:\n        default: value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_none(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='implementation: test_plugin.tasks.create\n'
                                     'inputs:\n    key: value',
            node_type2_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs:\n    key:\n        default: value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_operation_mapping_with_executor(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'inputs:\n    key: value',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'inputs:\n    key:\n        default: value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_operation(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'inputs:\n    key: value',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'inputs:\n    key:\n        default: value'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_no_op(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = self.create_parsed_operation({})
        expected_type_merger = self.create_parsed_operation({})

        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_operation_mapping(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs:\n    key:\n        default: value',
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent',
            'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_operation_mapping_no_inputs(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create',
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_none(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = None
        expected_type_merger = None
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_operation_mapping_with_executor(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_none_overrides_operation(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation=None,
            node_type2_operation=None
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_no_op(self):  # has analohe
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='implementation: test_plugin.tasks.create\n'
                                     'executor: host_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_operation_mapping(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs: {}',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'executor: host_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'executor: host_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_operation_mapping_no_inputs(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'executor: host_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'executor: host_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_none(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='implementation: test_plugin.tasks.create\n'
                                     'executor: host_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.create',
            'plugin': 'test_plugin',
            'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_operation_mapping_with_executor(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'executor: central_deployment_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'executor: central_deployment_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'central_deployment_agent',
            'executor': 'test_plugin'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_executor_overrides_operation(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'executor: central_deployment_agent\n'
                                     'inputs: {}',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'executor: central_deployment_agent\n'
                                 'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation({
            'operation': 'tasks.override_create',
            'plugin': 'test_plugin',
            'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_implementation_overrides_no_op(self):
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='inputs: {}\n'
                                     'executor: host_agent',
            add_plugin=False
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': '',
             'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_implementation_overrides_operation_mapping(self):
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs: {}',
            node_template1_operation='inputs:\n    key: value',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'key': 'value'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_implementation_overrides_operation_mapping_no_inputs(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create',
            node_template1_operation='executor: host_agent\n'
                                     'inputs: {}',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_implementation_overrides_none(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='executor: host_agent\n'
                                     'inputs: {}',
            add_plugin=False
        )
        expected_template_merger = self.create_parsed_operation(
            {'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_implementation_overrides_operation_mapping_with_executor(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='executor: central_deployment_agent\n'
                                     'inputs: {}'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_implementation_overrides_operation(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='executor: central_deployment_agent\n'
                                     'inputs: {}'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_no_inputs_overrides_no_op(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='',
            node_template1_operation='executor: host_agent',
            node_type2_operation='',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': '',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': ''})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_inputs_overrides_operation_mapping(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'inputs: {}',
            node_template1_operation='executor: host_agent',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_inputs_overrides_operation_mapping_no_inputs(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create',
            node_template1_operation='executor: host_agent',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_inputs_overrides_none(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation=None,
            node_template1_operation='executor: host_agent',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': '',
             'executor': 'host_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_inputs_overrides_operation_mapping_with_executor(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'executor: host_agent',
            node_template1_operation='executor: central_deployment_agent',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'host_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_no_inputs_overrides_operation(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='test_plugin.tasks.create',
            node_template1_operation='executor: central_deployment_agent',
            node_type2_operation='implementation: test_plugin.tasks.override_create',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_overrides_operation_mapping_with_retry(self):  # has analogue

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'max_retries: 1\n'
                                 'retry_interval: 2',
            node_template1_operation='inputs:\n    some: input',
            node_type2_operation='implementation: test_plugin.tasks.override_create',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'max_retries': 1,
             'retry_interval': 2,
             'inputs': {'some': 'input'}})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent'})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry(self):  # has analogue
        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'max_retries: 1\n'
                                 'retry_interval: 2',
            node_template1_operation='max_retries: 3\n'
                                     'retry_interval: 4',
            node_type2_operation='implementation: test_plugin.tasks.override_create\n'
                                 'max_retries: 3\n'
                                 'retry_interval: 4'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'max_retries': 3,
             'retry_interval': 4})
        expected_type_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'max_retries': 3,
             'retry_interval': 4})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger, expected_type_merger)

    def test_operation_mapping_with_retry_overrides_operation_mapping_with_retry_zero_values(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'max_retries: 1\n'
                                 'retry_interval: 2',
            node_template1_operation='max_retries: 0\n'
                                     'retry_interval: 0',
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'max_retries': 0,
             'retry_interval': 0})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

    def test_operation_mapping_with_impl_overrides_operation_mapping_with_retry(self):

        dsl_blueprint = self.create_dsl_blueprint(
            node_type1_operation='implementation: test_plugin.tasks.create\n'
                                 'max_retries: 1\n'
                                 'retry_interval: 2',
            node_template1_operation='implementation: test_plugin.tasks.override_create\n'
                                     'inputs:\n    some: input'
        )
        expected_template_merger = self.create_parsed_operation(
            {'operation': 'tasks.override_create',
             'plugin': 'test_plugin',
             'executor': 'central_deployment_agent',
             'inputs': {'some': 'input'}})
        self.assert_operation_merger(dsl_blueprint, expected_template_merger)

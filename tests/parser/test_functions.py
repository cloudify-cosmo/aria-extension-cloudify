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

from functools import partial
from ..suite import ParserTestCase


class FunctionsBaseTestCase(ParserTestCase):
    def assert_in_error_message(self, message, exc):
        self.assertIn(message, str(exc))


class TestGetProperty(FunctionsBaseTestCase):
    def test_illegal_property_in_property(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: { get_property: [SELF, notfound] }
"""
        self.assert_parser_raise_exception(
            exception_types=KeyError,
            extra_tests=[
                partial(self.assert_in_error_message, 'Node template property'),
                partial(self.assert_in_error_message, "doesn't exist"),
                partial(self.assert_in_error_message, 'vm.properties.notfound'),
                partial(self.assert_in_error_message, 'vm.properties.a'),
            ],
        )

    def test_illegal_property_in_interface(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    plugin:
        install: false
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
        interfaces:
            interface:
                op:
                    implementation: plugin.op
                    inputs:
                        x: { get_property: [vm, notfound] }
"""
        self.assert_parser_raise_exception(
            exception_types=KeyError,
            extra_tests=[
                partial(self.assert_in_error_message, 'Node template property'),
                partial(self.assert_in_error_message, "doesn't exist"),
                partial(self.assert_in_error_message, 'vm.properties.notfound'),
                partial(self.assert_in_error_message,
                        'vm.operations.interface.op.inputs.x'),
            ]
        )

    def test_illegal_property_in_output(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
outputs:
    a:
        value: { get_property: [vm, a] }
"""
        self.assert_parser_raise_exception(
            exception_types=KeyError,
            extra_tests=[
                partial(self.assert_in_error_message, 'Node template property'),
                partial(self.assert_in_error_message, "doesn't exist"),
                partial(self.assert_in_error_message, 'vm.properties.a'),
                partial(self.assert_in_error_message, 'outputs.a.value'),
            ]
        )


class TestGetAttribute(FunctionsBaseTestCase):
    def test_unknown_ref(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
outputs:
    a:
        value: { get_attribute: [i_do_not_exist, aaa] }
"""
        self.assert_parser_raise_exception(
            exception_types=KeyError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        "get_attribute function node reference "
                        "'i_do_not_exist' does not exist."),
            ]
        )

    def test_illegal_ref_in_node_template(self):
        def assert_with(ref):
            self.template.version_section('1.0')
            self.template += """
plugins:
    a:
        install: false
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
        interfaces:
            test:
                op:
                    implementation: a.a
                    inputs:
                        a: { get_attribute: [""" + ref + """, aaa] }

"""
            self.assert_parser_raise_exception(
                exception_types=ValueError,
                extra_tests=[
                    partial(self.assert_in_error_message,
                            '{0} cannot be used with get_attribute function '
                            'in vm.operations.test.op.inputs.a'.format(ref)),
                ]
            )
            self.template.clear()
        assert_with('SOURCE')
        assert_with('TARGET')

    def test_illegal_ref_in_relationship(self):
        def assert_with(ref):
            self.template.version_section('1.0')
            self.template += """
plugins:
    a:
        install: false
relationships:
    relationship: {}
node_types:
    vm_type:
        properties: {}
node_templates:
    node:
        type: vm_type
    vm:
        type: vm_type
        relationships:
            - target: node
              type: relationship
              source_interfaces:
                test:
                    op:
                        implementation: a.a
                        inputs:
                            a: { get_attribute: [""" + ref + """, aaa] }

"""
            self.assert_parser_raise_exception(
                exception_types=ValueError,
                extra_tests=[
                    partial(self.assert_in_error_message,
                            '{0} cannot be used with get_attribute function '
                            'in vm.relationship.test.op.inputs.a'.format(ref)),
                ]
            )
            self.template.clear()
        assert_with('SELF')

    def test_illegal_ref_in_outputs(self):
        def assert_with(ref):
            self.template.version_section('1.0')
            self.template += """
node_types:
    vm_type:
        properties: {}
node_templates:
    vm:
        type: vm_type
outputs:
    a:
        value: { get_attribute: [""" + ref + """, aaa] }
"""
            self.assert_parser_raise_exception(
                exception_types=ValueError,
                extra_tests=[
                    partial(self.assert_in_error_message,
                            '{0} cannot be used with get_attribute '
                            'function in outputs.a.value'.format(ref)),
                ]
            )
            self.template.clear()
        assert_with('SELF')
        assert_with('SOURCE')
        assert_with('TARGET')

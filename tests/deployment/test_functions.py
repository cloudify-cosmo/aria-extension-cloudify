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
from aria.exceptions import FunctionEvaluationError
from aria.parser.framework.functions import Concat
from aria.parser.dsl_supported_versions import VersionNumber, VersionStructure
from ..suite import PrepareDeploymentPlanTestCase, get_node_by_name


class FunctionsBaseTestCase(PrepareDeploymentPlanTestCase):
    def assert_in_error_message(self, message, exc):
        self.assertIn(message, str(exc))


class TestGetProperty(FunctionsBaseTestCase):
    def test_node_template_properties(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            ip: {}
            ip_duplicate: {}
    server_type:
        properties:
            endpoint: {}
node_templates:
    vm:
        type: vm_type
        properties:
            ip: 10.0.0.1
            ip_duplicate: { get_property: [ SELF, ip ] }
    server:
        type: server_type
        properties:
            endpoint: { get_property: [ vm, ip ] }
"""
        parsed = self.prepare_deployment_plan()
        vm = get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['properties']['ip_duplicate'])
        server = get_node_by_name(parsed, 'server')
        self.assertEqual('10.0.0.1', server['properties']['endpoint'])

    def test_node_template_properties_with_dsl_definitions(self):
        self.template.version_section('1.2')
        self.template += """
dsl_definitions:
    props: &props
        prop2: { get_property: [SELF, prop1] }
        prop3:
            nested: { get_property: [SELF, prop1] }
node_types:
    type1:
        properties:
            prop1: {}
            prop2: {}
            prop3: {}
node_templates:
    node1:
        type: type1
        properties:
            <<: *props
            prop1: value1
    node2:
        type: type1
        properties:
            <<: *props
            prop1: value2
"""
        plan = self.prepare_deployment_plan()
        props1 = get_node_by_name(plan, 'node1')['properties']
        props2 = get_node_by_name(plan, 'node2')['properties']
        self.assertEqual({
            'prop1': 'value1',
            'prop2': 'value1',
            'prop3': {'nested': 'value1'},
        }, props1)
        self.assertEqual({
            'prop1': 'value2',
            'prop2': 'value2',
            'prop3': {'nested': 'value2'},
        }, props2)

    def test_node_template_interfaces(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    plugin:
        install: false
node_types:
    vm_type:
        properties:
            ip:
                type: string
node_templates:
    vm:
        type: vm_type
        properties:
            ip: 10.0.0.1
        interfaces:
            interface:
                op:
                    implementation: plugin.op
                    inputs:
                        x: { get_property: [vm, ip] }
"""
        parsed = self.prepare_deployment_plan()
        vm = get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['operations']['op']['inputs']['x'])
        self.assertEqual('10.0.0.1', vm['operations']['interface.op']['inputs']['x'])

    def test_node_template_interfaces_with_dsl_definitions(self):
        self.template.version_section('1.2')
        self.template += """
dsl_definitions:
    op: &op
        implementation: plugin.op
        inputs:
            x: { get_property: [SELF, prop1] }
plugins:
    plugin:
        install: false
node_types:
    type1:
        properties:
            prop1: {}
node_templates:
    node1:
        type: type1
        properties:
            prop1: value1
        interfaces:
            interface:
                op: *op
    node2:
        type: type1
        properties:
            prop1: value2
        interfaces:
            interface:
                op: *op
"""
        parsed = self.prepare_deployment_plan()
        node1 = get_node_by_name(parsed, 'node1')
        node2 = get_node_by_name(parsed, 'node2')
        self.assertEqual('value1', node1['operations']['op']['inputs']['x'])
        self.assertEqual('value1', node1['operations']['interface.op']['inputs']['x'])
        self.assertEqual('value2', node2['operations']['op']['inputs']['x'])
        self.assertEqual('value2', node2['operations']['interface.op']['inputs']['x'])

    def test_node_template_capabilities(self):
        self.template.version_section('1.2')
        self.template += """
node_templates:
    node:
        type: type
        capabilities:
            scalable:
                properties:
                    default_instances: { get_property: [node, prop1] }
                    max_instances: { get_property: [SELF, prop1] }
                    min_instances: { get_input: my_input }
inputs:
    my_input:
        default: 20
node_types:
    type:
        properties:
            prop1:
                default: 10
"""
        parsed = self.prepare_deployment_plan()
        node = get_node_by_name(parsed, 'node')
        self.assertEqual({
            'default_instances': 10,
            'min_instances': 20,
            'max_instances': 10,
            'current_instances': 10,
            'planned_instances': 10,
        }, node['capabilities']['scalable']['properties'])

    def test_policies_properties(self):
        self.template.version_section('1.2')
        self.template += """
node_templates:
    node:
        type: type
inputs:
    my_input:
        default: 20
node_types:
    type:
        properties:
            prop1:
                default: 10
groups:
    group:
        members: [node]
policies:
    policy:
        type: tosca.policies.Scaling
        targets: [group]
        properties:
            default_instances: { get_property: [node, prop1] }
            min_instances: { get_input: my_input }
"""
        parsed = self.prepare_deployment_plan()
        expected = {
            'default_instances': 10,
            'min_instances': 20,
            'max_instances': -1,
            'current_instances': 10,
            'planned_instances': 10,
        }
        self.assertEqual(expected, parsed['scaling_groups']['group']['properties'])
        self.assertEqual(expected, parsed['policies']['policy']['properties'])

    def test_recursive(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    i:
        default: 1
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
            x: { type: string }
            y: { type: string }
            z: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 0
            b: { get_property: [ SELF, a ] }
            c: { get_property: [ SELF, b ] }
            x: { get_property: [ SELF, z ] }
            y: { get_property: [ SELF, x ] }
            z: { get_input: i }
"""
        parsed = self.prepare_deployment_plan()
        vm = get_node_by_name(parsed, 'vm')
        self.assertEqual(0, vm['properties']['b'])
        self.assertEqual(1, vm['properties']['x'])
        self.assertEqual(1, vm['properties']['y'])
        self.assertEqual(1, vm['properties']['z'])

    def test_outputs(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 0
            b: { get_property: [vm, a] }
outputs:
    a:
        value: { get_property: [vm, a] }
    b:
        value: { get_property: [vm, b] }
"""
        parsed = self.prepare_deployment_plan()
        self.assertEqual(0, parsed.outputs['a']['value'])
        self.assertEqual(0, parsed.outputs['b']['value'])

    def test_source_and_target_interfaces(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    plugin:
        source: dummy
node_types:
    some_type:
        properties:
            a: { type: string }
relationships:
    tosca.relationships.HostedOn: {}
    rel:
        derived_from: tosca.relationships.HostedOn
        source_interfaces:
            source_interface:
                op1:
                    implementation: plugin.operation
                    inputs:
                        source_a:
                            default: { get_property: [%(source)s, a] }
                        target_a:
                            default: { get_property: [%(target)s, a] }
        target_interfaces:
            target_interface:
                op2:
                    implementation: plugin.operation
                    inputs:
                        source_a:
                            default: { get_property: [%(source)s, a] }
                        target_a:
                            default: { get_property: [%(target)s, a] }
node_templates:
    node1:
        type: some_type
        properties:
            a: 1
    node2:
        type: some_type
        properties:
            a: 2
        relationships:
            -   type: rel
                target: node1
"""

        def do_assertions():
            """
            Assertions are made for explicit node names in a relationship
            and another time for SOURCE & TARGET keywords.
            """
            node = get_node_by_name(prepared, 'node2')
            source_ops = node['relationships'][0]['source_operations']
            self.assertEqual(
                2,
                source_ops['source_interface.op1']['inputs']['source_a'])
            self.assertEqual(
                1,
                source_ops['source_interface.op1']['inputs']['target_a'])
            target_ops = node['relationships'][0]['target_operations']
            self.assertEqual(
                2,
                target_ops['target_interface.op2']['inputs']['source_a'])
            self.assertEqual(
                1,
                target_ops['target_interface.op2']['inputs']['target_a'])

        # Explicit node template names
        prepared = self.prepare_deployment_plan(
            parse_kwargs={'template_inputs': {'source': 'node2', 'target': 'node1'}},
        )
        do_assertions()

        # SOURCE & TARGET
        prepared = self.prepare_deployment_plan(
            parse_kwargs={'template_inputs': {'source': 'SOURCE', 'target': 'TARGET'}},
        )
        do_assertions()

    def test_recursive_with_nesting(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 1
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, a ] }, 2 ]
"""
        parsed = self.prepare_deployment_plan()
        vm = get_node_by_name(parsed, 'vm')
        self.assertEqual(1, vm['properties']['b'][0])
        self.assertEqual(2, vm['properties']['b'][1])
        self.assertEqual(1, vm['properties']['c'][0])
        self.assertEqual(2, vm['properties']['c'][1])

    def test_circular_get_property(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: { get_property: [SELF, b] }
            b: { get_property: [SELF, c] }
            c: { get_property: [SELF, a] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'Circular get_property function call detected'),
            ]
        )

    def test_circular_get_property_with_nesting(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, b ] }, 2 ]
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'Circular get_property function call detected'),
            ]
        )

    def test_not_circular_nested_property_path(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
node_templates:
    vm1:
        type: vm_type
        properties:
            a: { get_property: [ vm2, a ] }
            b: bla1
    vm2:
        type: vm_type
        properties:
            a:
                b3:
                    b4: { get_property: [ vm1, b ] }
            b: bla2
"""
        self.prepare_deployment_plan()

    def test_recursive_get_property_in_outputs(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a: 1
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, a ] }, 2 ]
outputs:
    o:
        value:
            a: { get_property: [vm, b] }
            b: [0, { get_property: [vm, b] }]
"""
        parsed = self.prepare_deployment_plan()
        outputs = parsed.outputs
        self.assertEqual(1, outputs['o']['value']['a'][0])
        self.assertEqual(2, outputs['o']['value']['a'][1])
        self.assertEqual(0, outputs['o']['value']['b'][0])
        self.assertEqual(1, outputs['o']['value']['b'][1][0])
        self.assertEqual(2, outputs['o']['value']['b'][1][1])

    def test_circular_get_property_from_outputs(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            b: { type: string }
            c: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            b: { get_property: [SELF, c] }
            c: [ { get_property: [SELF, b ] }, 2 ]
outputs:
    o:
        value:
            a: 1
            b: { get_property: [vm, b] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'Circular get_property function call detected'),
            ]
        )

    def test_circular_self_get_property(self):
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
            a: [ { get_property: [SELF, a ] } ]
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'Circular get_property function call detected'),
            ]
        )

    def test_nested_property_path(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            endpoint: {}
            a: { type: integer }
            b: {}
            c: {}
    server_type:
        properties:
            port: { type: integer }
node_templates:
    vm:
        type: vm_type
        properties:
            endpoint:
                url:
                    protocol: http
                port: 80
                names: [site1, site2, site3]
                pairs:
                    - key: key1
                      value: value1
                    - key: key2
                      value: value2
            a: { get_property: [ SELF, endpoint, port ] }
            b: { get_property: [ SELF, endpoint, names, 0 ] }
            c: { get_property: [ SELF, endpoint, pairs, 1 , key] }
    server:
        type: server_type
        properties:
            port: { get_property: [ vm, endpoint, port ] }
outputs:
    a:
        value: { get_property: [ vm, endpoint, port ] }
    b:
        value: { get_property: [ vm, endpoint, url, protocol ] }
    c:
        value: { get_property: [ vm, endpoint, names, 1 ] }
    d:
        value: { get_property: [ vm, endpoint, pairs, 1, value] }

"""
        parsed = self.prepare_deployment_plan()
        vm = get_node_by_name(parsed, 'vm')
        self.assertEqual(80, vm['properties']['a'])
        self.assertEqual('site1', vm['properties']['b'])
        self.assertEqual('key2', vm['properties']['c'])
        server = get_node_by_name(parsed, 'server')
        self.assertEqual(80, server['properties']['port'])
        self.assertEqual(80, parsed.outputs['a']['value'])
        self.assertEqual('http', parsed.outputs['b']['value'])
        self.assertEqual('site2', parsed.outputs['c']['value'])
        self.assertEqual('value2', parsed.outputs['d']['value'])

    def test_invalid_nested_property1(self):
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
            a:
                a0: { get_property: [ SELF, a, notfound ] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=KeyError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        "Node template property 'vm.properties.a.notfound' "
                        "referenced from 'vm.properties.a.a0' doesn't exist."),
            ]
        )

    def test_invalid_nested_property2(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: {}
            b: {}
node_templates:
    vm:
        type: vm_type
        properties:
            a: [1,2,3]
            b: { get_property: [SELF, a, b] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=TypeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'is expected b to be an int but it is a str'),
            ]
        )

    def test_invalid_nested_property3(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: {}
            b: {}
node_templates:
    vm:
        type: vm_type
        properties:
            a: [1,2,3]
            b: { get_property: [SELF, a, 10] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=IndexError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'index is out of range. Got 10 but list size is 3'),
            ]
        )

    def test_circular_nested_property_path(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    vm_type:
        properties:
            a: { type: string }
            b: { type: string }
node_templates:
    vm:
        type: vm_type
        properties:
            a:
                a0: { get_property: [ SELF, b, b0 ] }
            b:
                b0: { get_property: [ SELF, a, a0 ] }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message,
                        'Circular get_property function call detected: '
                        'vm.b,b0 -> vm.a,a0 -> vm.b,b0'),
            ]
        )


class TestConcat(FunctionsBaseTestCase):
    def test_invalid_version(self):
        try:
            Concat.supported_version = VersionStructure(
                profile='unit_test_profile',
                number=VersionNumber(1, 1, 0))
            self.template.version_section('1.0')
            self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: { concat: [1, 2] }
"""
            self.assert_prepare_deployment_raise_exception(
                exception_types=FunctionEvaluationError,
                extra_tests=[
                    partial(self.assert_in_error_message, 'version 1_1 or greater'),
                ]

            )
        finally:
            Concat.supported_version = None

    def test_invalid_concat(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: { concat: 1 }
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=ValueError,
            extra_tests=[
                partial(self.assert_in_error_message, 'Illegal'),
                partial(self.assert_in_error_message, 'concat'),
            ]

        )

    def test_node_template_properties_simple(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: { concat: [one, two, three] }
"""
        parsed = self.prepare_deployment_plan()
        node = get_node_by_name(parsed, 'node')
        self.assertEqual('onetwothree', node['properties']['property'])

    def test_node_template_properties_with_self_property(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property1: {}
            property2: {}
node_templates:
    node:
        type: type
        properties:
            property1: value1
            property2: { concat:
                [one, { get_property: [SELF, property1] }, three]
            }
"""
        parsed = self.prepare_deployment_plan()
        node = get_node_by_name(parsed, 'node')
        self.assertEqual('onevalue1three', node['properties']['property2'])

    def test_node_template_properties_with_named_node_property(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: { concat:
                [one, { get_property: [node2, property] }, three]
            }
    node2:
        type: type
        properties:
            property: value2
"""
        parsed = self.prepare_deployment_plan()
        node = get_node_by_name(parsed, 'node')
        self.assertEqual('onevalue2three', node['properties']['property'])

    def test_node_template_properties_with_invalid_node_property_cycle(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property1: {}
            property2: {}
node_templates:
    node1:
        type: type
        properties:
            property1: { concat:
                [one, { get_property: [node2, property1] }, three]
            }
            property2: value1
    node2:
        type: type
        properties:
            property1: { concat:
                [one, { get_property: [node1, property1] }, three]
            }
            property2: value2
"""
        self.assert_prepare_deployment_raise_exception(
            exception_types=RuntimeError,
            extra_tests=[
                partial(self.assert_in_error_message, 'Circular'),
            ]

        )

    def test_node_template_properties_with_recursive_concat(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node1:
        type: type
        properties:
            property: { concat:
                [one, { get_property: [node2, property] }, three]
            }
    node2:
        type: type
        properties:
            property: { concat: [one, two, three] }
"""
        parsed = self.prepare_deployment_plan()
        node1 = get_node_by_name(parsed, 'node1')
        node2 = get_node_by_name(parsed, 'node2')
        self.assertEqual('oneonetwothreethree', node1['properties']['property'])
        self.assertEqual('onetwothree', node2['properties']['property'])

    def test_node_operation_inputs(self):
        self.template.version_section('1.1')
        self.template += """
plugins:
    p:
        install: false
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: value
        interfaces:
            interface:
                op:
                    implementation: p.task
                    inputs:
                        input1: { concat: [one,
                            { get_property: [SELF, property] }, three] }
                        input2:
                            key1: value1
                            key2: { concat: [one,
                                { get_property: [SELF, property] }, three] }
                            key3:
                                - item1
                                - { concat: [one,
                                    {get_property: [SELF, property] },three]}
                        input3: { concat: [one,
                                    {get_property: [SELF, property] },
                                    {get_attribute: [SELF, attribute] }]}
"""
        parsed = self.prepare_deployment_plan()
        inputs = get_node_by_name(parsed, 'node')['operations']['interface.op']['inputs']
        self.assertEqual('onevaluethree', inputs['input1'])
        self.assertEqual('onevaluethree', inputs['input2']['key2'])
        self.assertEqual('onevaluethree', inputs['input2']['key3'][1])
        self.assertEqual(
            {'concat': ['one', 'value', {'get_attribute': ['SELF', 'attribute']}]},
            inputs['input3'])

    def test_relationship_operation_inputs(self):
        self.template.version_section('1.1')
        self.template += """
plugins:
    p:
        install: false
node_types:
    type:
        properties:
            property: {}
relationships:
    tosca.relationships.HostedOn: {}
node_templates:
    node:
        type: type
        properties:
            property: value
        relationships:
            -   type: tosca.relationships.HostedOn
                target: node2
                source_interfaces:
                    interface:
                        op:
                            implementation: p.task
                            inputs:
                                input1: { concat: [one,
                                    { get_property: [SOURCE, property] },
                                    three] }
                                input2:
                                    key1: value1
                                    key2: { concat: [one,
                                        { get_property: [SOURCE, property] },
                                        three] }
                                    key3:
                                        - item1
                                        - { concat: [one,
                                            {get_property: [TARGET, property]},
                                            three] }
                                input3: { concat: [one,
                                    {get_property: [SOURCE, property] },
                                    {get_attribute: [SOURCE, attribute] }]}
    node2:
        type: type
        properties:
            property: value2
"""
        parsed = self.prepare_deployment_plan()
        node = get_node_by_name(parsed, 'node')
        inputs = node['relationships'][0]['source_operations']['interface.op']['inputs']
        self.assertEqual('onevaluethree', inputs['input1'])
        self.assertEqual('onevaluethree', inputs['input2']['key2'])
        self.assertEqual('onevalue2three', inputs['input2']['key3'][1])
        self.assertEqual(
            {'concat': ['one', 'value', {'get_attribute': ['SOURCE', 'attribute']}]},
            inputs['input3'])

    def test_outputs(self):
        self.template.version_section('1.1')
        self.template += """
node_types:
    type:
        properties:
            property: {}
node_templates:
    node:
        type: type
        properties:
            property: value
outputs:
    output1:
        value: { concat: [one,
                          {get_property: [node, property]},
                          three] }
    output2:
        value:
            - item1
            - { concat: [one,
                         {get_property: [node, property]},
                         three] }
    output3:
        value: { concat: [one,
                          {get_property: [node, property]},
                          {get_attribute: [node, attribute]}] }
"""
        parsed = self.prepare_deployment_plan()
        outputs = parsed['outputs']
        self.assertEqual('onevaluethree', outputs['output1']['value'])
        self.assertEqual('onevaluethree', outputs['output2']['value'][1])
        self.assertEqual(
            {'concat': ['one', 'value', {'get_attribute': ['node', 'attribute']}]},
            outputs['output3']['value'])

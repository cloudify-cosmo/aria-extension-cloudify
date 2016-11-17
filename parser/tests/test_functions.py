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

from dsl_parser.tasks import prepare_deployment_plan
from framework.abstract_test_parser import AbstractTestParser
from framework.abstract_test_parser import timeout


class TestGetProperty(AbstractTestParser):

    def test_node_template_properties(self):
        yaml = """
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
        v = self.parse(yaml)
        parsed = prepare_deployment_plan(v)
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['properties']['ip_duplicate'])
        server = self.get_node_by_name(parsed, 'server')
        self.assertEqual('10.0.0.1', server['properties']['endpoint'])

    def test_node_template_properties_with_dsl_definitions(self):
        yaml = """
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
        plan = prepare_deployment_plan(self.parse_1_2(yaml))
        props1 = self.get_node_by_name(plan, 'node1')['properties']
        props2 = self.get_node_by_name(plan, 'node2')['properties']
        self.assertEqual({
            'prop1': 'value1',
            'prop2': 'value1',
            'prop3': {'nested': 'value1'}
        }, props1)
        self.assertEqual({
            'prop1': 'value2',
            'prop2': 'value2',
            'prop3': {'nested': 'value2'}
        }, props2)

    def test_illegal_property_in_property(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_node_template_interfaces(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual('10.0.0.1', vm['operations']['op']['inputs']['x'])
        self.assertEqual('10.0.0.1',
                         vm['operations']['interface.op']['inputs']['x'])

    def test_node_template_interfaces_with_dsl_definitions(self):
        yaml = """
dsl_definitions:
    op: &op
        implementation: plugin.op
        inputs:
            x: { get_property: [SELF, prop1] }
plugins:
    plugin:
        executor: central_deployment_agent
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
        parsed = prepare_deployment_plan(self.parse_1_2(yaml))
        node1 = self.get_node_by_name(parsed, 'node1')
        node2 = self.get_node_by_name(parsed, 'node2')
        self.assertEqual('value1', node1['operations']['op']['inputs']['x'])
        self.assertEqual('value1',
                         node1['operations']['interface.op']['inputs']['x'])
        self.assertEqual('value2', node2['operations']['op']['inputs']['x'])
        self.assertEqual('value2',
                         node2['operations']['interface.op']['inputs']['x'])

    def test_illegal_property_in_interface(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_node_template_capabilities(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_3(yaml))
        node = self.get_node_by_name(parsed, 'node')
        self.assertEqual({
            'default_instances': 10,
            'min_instances': 20,
            'max_instances': 10,
            'current_instances': 10,
            'planned_instances': 10,
        }, node['capabilities']['scalable']['properties'])

    def test_policies_properties(self):
        yaml = """
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
        type: cloudify.policies.scaling
        targets: [group]
        properties:
            default_instances: { get_property: [node, prop1] }
            min_instances: { get_input: my_input }
"""
        parsed = prepare_deployment_plan(self.parse_1_3(yaml))
        expected = {
            'default_instances': 10,
            'min_instances': 20,
            'max_instances': -1,
            'current_instances': 10,
            'planned_instances': 10,
        }
        self.assertEqual(expected,
                         parsed['scaling_groups']['group']['properties'])
        self.assertEqual(expected, parsed['policies']['policy']['properties'])

    def test_recursive(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(0, vm['properties']['b'])
        self.assertEqual(1, vm['properties']['x'])
        self.assertEqual(1, vm['properties']['y'])
        self.assertEqual(1, vm['properties']['z'])

    def test_outputs(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        outputs = parsed.outputs
        self.assertEqual(0, outputs['a']['value'])
        self.assertEqual(0, outputs['b']['value'])

    def test_illegal_property_in_output(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_source_and_target_interfaces(self):
        yaml = """
plugins:
    plugin:
        executor: central_deployment_agent
        source: dummy
node_types:
    some_type:
        properties:
            a: { type: string }
relationships:
    cloudify.relationships.contained_in: {}
    rel:
        derived_from: cloudify.relationships.contained_in
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
            node = self.get_node_by_name(prepared, 'node2')
            source_ops = node['relationships'][0]['source_operations']
            self.assertEqual(2,
                             source_ops['source_interface.op1']['inputs']
                             ['source_a'])
            self.assertEqual(1,
                             source_ops['source_interface.op1']['inputs']
                             ['target_a'])
            target_ops = node['relationships'][0]['target_operations']
            self.assertEqual(2,
                             target_ops['target_interface.op2']['inputs']
                             ['source_a'])
            self.assertEqual(1,
                             target_ops['target_interface.op2']['inputs']
                             ['target_a'])

        # Explicit node template names
        prepared = prepare_deployment_plan(self.parse(yaml % {
            'source': 'node2', 'target': 'node1'}))
        do_assertions()

        # SOURCE & TARGET
        prepared = prepare_deployment_plan(self.parse(yaml % {
            'source': 'SOURCE', 'target': 'TARGET'}))
        do_assertions()

    def test_recursive_with_nesting(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(1, vm['properties']['b'][0])
        self.assertEqual(2, vm['properties']['b'][1])
        self.assertEqual(1, vm['properties']['c'][0])
        self.assertEqual(2, vm['properties']['c'][1])

    @timeout(seconds=10)
    def test_circular_get_property(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    @timeout(seconds=10)
    def test_circular_get_property_with_nesting(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_recursive_get_property_in_outputs(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        outputs = parsed.outputs
        self.assertEqual(1, outputs['o']['value']['a'][0])
        self.assertEqual(2, outputs['o']['value']['a'][1])
        self.assertEqual(0, outputs['o']['value']['b'][0])
        self.assertEqual(1, outputs['o']['value']['b'][1][0])
        self.assertEqual(2, outputs['o']['value']['b'][1][1])

    @timeout(seconds=10)
    def test_circular_get_property_from_outputs(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    @timeout(seconds=10)
    def test_circular_self_get_property(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_nested_property_path(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse(yaml))
        vm = self.get_node_by_name(parsed, 'vm')
        self.assertEqual(80, vm['properties']['a'])
        self.assertEqual('site1', vm['properties']['b'])
        self.assertEqual('key2', vm['properties']['c'])
        server = self.get_node_by_name(parsed, 'server')
        self.assertEqual(80, server['properties']['port'])
        outputs = parsed.outputs
        self.assertEqual(80, outputs['a']['value'])
        self.assertEqual('http', outputs['b']['value'])
        self.assertEqual('site2', outputs['c']['value'])
        self.assertEqual('value2', outputs['d']['value'])

    def test_invalid_nested_property1(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_invalid_nested_property2(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    def test_invalid_nested_property3(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    @timeout(seconds=10)
    def test_circular_nested_property_path(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"]
        )

    @timeout(seconds=10)
    def test_not_circular_nested_property_path(self):
        yaml = """
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
        prepare_deployment_plan(self.parse(yaml))


class TestGetAttribute(AbstractTestParser):

    def test_unknown_ref(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["function \"get_attribute\" parameter 1 is not a "
                            "valid modelable entity name: 'i_do_not_exist'"]
        )

    def test_illegal_ref_in_node_template(self):
        def assert_with(ref):
            yaml = """
plugins:
    a:
        executor: central_deployment_agent
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
            self.assert_parser_issue_messages(
                dsl_string=yaml,
                issue_messages=["function \"get_attribute\" parameter 1 "
                                "can be \"{0}\" only in a relationship template".format(ref)]
            )
        assert_with('SOURCE')
        assert_with('TARGET')

    def test_illegal_ref_in_relationship(self):
        def assert_with(ref):
            yaml = """
plugins:
    a:
        executor: central_deployment_agent
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
            self.assert_parser_issue_messages(
                dsl_string=yaml,
                issue_messages=["f"]
            )
        assert_with('SELF')

    def test_illegal_ref_in_outputs(self):
        def assert_with(ref):
            yaml = """
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

            expected_node_template_issue = " "
            if ref == 'SELF':
                expected_node_template_issue = " a node template or "

            self.assert_parser_issue_messages(
                dsl_string=yaml,
                issue_messages=["function \"get_attribute\" parameter 1 "
                                "can be \"{0}\" only in{1}a relationship "
                                "template".format(ref, expected_node_template_issue)]
            )
        assert_with('SELF')
        assert_with('SOURCE')
        assert_with('TARGET')


class TestConcat(AbstractTestParser):

    def test_invalid_version(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"],
            additional_parsing_arguments={'dsl_version': self.BASIC_VERSION_SECTION_DSL_1_0}
        )

    def test_invalid_concat(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["function \"concat\" argument must "
                            "be a list of string expressions: 1"],
            parsing_method=self.parse_1_1
        )

    def test_node_template_properties_simple(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        node = self.get_node_by_name(parsed, 'node')
        self.assertEqual('onetwothree', node['properties']['property'])

    def test_node_template_properties_with_self_property(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        node = self.get_node_by_name(parsed, 'node')
        self.assertEqual('onevalue1three', node['properties']['property2'])

    def test_node_template_properties_with_named_node_property(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        node = self.get_node_by_name(parsed, 'node')
        self.assertEqual('onevalue2three', node['properties']['property'])

    def test_node_template_properties_with_invalid_node_property_cycle(self):
        yaml = """
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
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"],
            parsing_method=self.parse_1_1
        )

    def test_node_template_properties_with_recursive_concat(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        node1 = self.get_node_by_name(parsed, 'node1')
        node2 = self.get_node_by_name(parsed, 'node2')
        self.assertEqual('oneonetwothreethree',
                         node1['properties']['property'])
        self.assertEqual('onetwothree', node2['properties']['property'])

    def test_node_operation_inputs(self):
        yaml = """
plugins:
    p:
        executor: central_deployment_agent
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        inputs = self.get_node_by_name(parsed, 'node')['operations'][
            'interface.op']['inputs']
        self.assertEqual('onevaluethree', inputs['input1'])
        self.assertEqual('onevaluethree', inputs['input2']['key2'])
        self.assertEqual('onevaluethree', inputs['input2']['key3'][1])
        self.assertEqual({'concat':
                         ['one', 'value', {'get_attribute': ['SELF',
                                                             'attribute']}]},
                         inputs['input3'])

    def test_relationship_operation_inputs(self):
        yaml = """
plugins:
    p:
        executor: central_deployment_agent
        install: false
node_types:
    type:
        properties:
            property: {}
relationships:
    cloudify.relationships.contained_in: {}
node_templates:
    node:
        type: type
        properties:
            property: value
        relationships:
            -   type: cloudify.relationships.contained_in
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        inputs = self.get_node_by_name(parsed, 'node')['relationships'][0][
            'source_operations']['interface.op']['inputs']
        self.assertEqual('onevaluethree', inputs['input1'])
        self.assertEqual('onevaluethree', inputs['input2']['key2'])
        self.assertEqual('onevalue2three', inputs['input2']['key3'][1])
        self.assertEqual({'concat':
                         ['one', 'value', {'get_attribute': ['SOURCE',
                                                             'attribute']}]},
                         inputs['input3'])

    def test_outputs(self):
        yaml = """
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
        parsed = prepare_deployment_plan(self.parse_1_1(yaml))
        outputs = parsed['outputs']
        self.assertEqual('onevaluethree', outputs['output1']['value'])
        self.assertEqual('onevaluethree', outputs['output2']['value'][1])
        self.assertEqual({'concat':
                         ['one', 'value', {'get_attribute': ['node',
                                                             'attribute']}]},
                         outputs['output3']['value'])

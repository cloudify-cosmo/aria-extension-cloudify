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

from aria.parser.constants import DEPLOYMENT_PLUGINS_TO_INSTALL

from .suite import ParserTestCase, op_struct, get_nodes_by_names


class NodePluginsToInstallTest(ParserTestCase):
    def test_no_duplicate_node_plugins_to_install_field_from_relationship(self):  # NOQA
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: tosca.nodes.Compute
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
        relationships:
            - type: tosca.relationships.my_relationship
              target: test_node2
    test_node2:
        type: tosca.nodes.Compute

node_types:
    tosca.nodes.Compute: {}

plugins:
    test_plugin:
        source: dummy

relationships:
    tosca.relationships.my_relationship:
        source_interfaces:
            tosca.interfaces.relationship_lifecycle:
                postconfigure:
                    implementation: test_plugin.task.postconfigure
                    inputs: {}
"""
        result = self.parse()
        node = [n for n in result['nodes'] if n['name'] == 'test_node1'][0]
        plugin = node['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(node['plugins_to_install']))

    def test_node_plugins_to_install_field_from_relationship(self):
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: tosca.nodes.Compute
        relationships:
            - type: tosca.relationships.my_relationship
              target: test_node2
    test_node2:
        type: tosca.nodes.Compute

node_types:
    tosca.nodes.Compute: {}

plugins:
    test_plugin:
        source: dummy

relationships:
    tosca.relationships.my_relationship:
        source_interfaces:
            tosca.interfaces.relationship_lifecycle:
                postconfigure:
                    implementation: test_plugin.task.postconfigure
                    inputs: {}
"""
        result = self.parse()
        node = [n for n in result['nodes'] if n['name'] == 'test_node1'][0]
        plugin = node['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(node['plugins_to_install']))

    def test_node_plugins_to_install_field(self):
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: tosca.nodes.Compute
node_types:
    tosca.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
plugins:
    test_plugin:
        source: dummy
"""
        result = self.parse()
        plugin = result['nodes'][0]['plugins_to_install'][0]
        self.assertEquals('test_plugin', plugin['name'])
        self.assertEquals(1, len(result['nodes'][0]['plugins_to_install']))

    def test_node_plugins_to_install_field_plugins_from_contained_nodes(self):
        def get_plugin_to_install_from_node(node, plugin_name):
            for plugin in node['plugins_to_install']:
                if plugin['name'] == plugin_name:
                    return plugin

        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: tosca.nodes.Compute
    test_node2:
        type: test_type
        relationships:
            -   type: tosca.relationships.HostedOn
                target: test_node1
    test_node3:
        type: test_type2
        relationships:
            -   type: tosca.relationships.HostedOn
                target: test_node2
    test_node4:
        type: test_type
        relationships:
            -   type: tosca.relationships.HostedOn
                target: test_node3
node_types:
    tosca.nodes.Compute: {}
    test_type:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}
    test_type2:
        interfaces:
            test_interface2:
                install:
                    implementation: test_plugin2.install
                    inputs: {}
relationships:
    tosca.relationships.HostedOn: {}
plugins:
    test_plugin:
        source: dummy
    test_plugin2:
        source: dummy
"""
        result = self.parse()
        self.assertEquals(4, len(result['nodes']))
        nodes = get_nodes_by_names(
            result, ['test_node1', 'test_node2', 'test_node3', 'test_node4'])

        # ensuring non-host nodes don't have this field
        self.assertTrue('plugins_to_install' not in nodes[1])
        node = nodes[2]
        test_plugin = get_plugin_to_install_from_node(node, 'test_plugin')
        test_plugin2 = get_plugin_to_install_from_node(node, 'test_plugin2')
        self.assertEquals('test_plugin', test_plugin['name'])
        self.assertEquals('test_plugin2', test_plugin2['name'])
        self.assertEquals(2, len(nodes[2]['plugins_to_install']))

    def test_instance_relationships_target_node_plugins(self):
        self.template.version_section('1.0')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    test_node2:
        type: test_type
        relationships:
            -   type: test_relationship
                target: test_node
                source_interfaces:
                    test_interface1:
                        install: test_plugin1.install
            -   type: test_relationship
                target: test_node
                target_interfaces:
                    test_interface1:
                        install: test_plugin2.install
relationships:
    test_relationship: {}
plugins:
    test_plugin1:
        source: dummy
    test_plugin2:
        source: dummy
"""
        result = self.parse()
        self.assertEquals(2, len(result['nodes']))
        nodes = get_nodes_by_names(result, ['test_node', 'test_node2'])
        self.assertEquals('test_node2', nodes[0]['id'])
        self.assertEquals(2, len(nodes[0]['relationships']))

        relationship1 = nodes[0]['relationships'][0]
        self.assertEquals('test_relationship', relationship1['type'])
        self.assertEquals('test_node', relationship1['target_id'])
        rel1_source_ops = relationship1['source_operations']
        self.assertEqual(op_struct('test_plugin1', 'install'),
                         rel1_source_ops['install'])
        self.assertEqual(op_struct('test_plugin1', 'install'),
                         rel1_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel1_source_ops))
        self.assertEquals(8, len(relationship1))
        plugin1_def = nodes[0]['plugins'][0]
        self.assertEquals('test_plugin1', plugin1_def['name'])

        relationship2 = nodes[0]['relationships'][1]
        self.assertEquals('test_relationship', relationship2['type'])
        self.assertEquals('test_node', relationship2['target_id'])
        rel2_source_ops = relationship2['target_operations']
        self.assertEqual(op_struct('test_plugin2', 'install'),
                         rel2_source_ops['install'])
        self.assertEqual(op_struct('test_plugin2', 'install'),
                         rel2_source_ops['test_interface1.install'])
        self.assertEquals(2, len(rel2_source_ops))
        self.assertEquals(8, len(relationship2))

        # expecting the other plugin to be under test_node rather than
        # test_node2:
        plugin2_def = nodes[1]['plugins'][1]
        self.assertEquals('test_plugin2', plugin2_def['name'])


class DeploymentPluginsToInstallTest(ParserTestCase):
    def test_no_operation_mapping_no_plugin(self):
        self.template.version_section('1.0')
        self.template += """
node_templates:
    test_node1:
        type: tosca.nodes.Compute

node_types:
    tosca.nodes.Compute:
        interfaces:
            test_interface:
                start:
                    implementation: test_plugin.start
                    inputs: {}

plugins:
    test_management_plugin:
        source: dummy
    test_plugin:
        source: dummy
"""
        result = self.parse()
        deployment_plugins = result['nodes'][0][DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(0, len(deployment_plugins))

        # check the property on the plan is correct
        deployment_plugins = result[DEPLOYMENT_PLUGINS_TO_INSTALL]
        self.assertEquals(0, len(deployment_plugins))

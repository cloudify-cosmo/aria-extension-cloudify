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

from cloudify.framework.abstract_test_parser import AbstractTestParser
from cloudify.suite import TempDirectoryTestCase


class InterfaceMergerTest(AbstractTestParser, TempDirectoryTestCase):

    def test_merge_and_override_operations(self):

        imported_yaml = """
node_types:
    type_a:
        interfaces:
            interface_a:
                op_a:
                    implementation: test_plugin.install.aa
                    inputs: {}
                op_b:
                    implementation: test_plugin.install.ab
                    inputs: {}
                op_c:
                    implementation: test_plugin.install.ac
                    inputs: {}
        """

        yaml = self.create_yaml_with_imports([imported_yaml]) + self.BASIC_PLUGIN + """
node_types:
    type_b:
        derived_from: type_a
        interfaces:
            interface_a:
                op_a:
                    implementation: test_plugin.install.ba
                    inputs: {}
                op_d:
                    implementation: test_plugin.install.bd
                    inputs: {}
node_templates:
    template_c:
        type: type_b
        interfaces:
            interface_a:
                op_b:
                    implementation: test_plugin.install.cb
                    inputs: {}
                op_e:
                    implementation: test_plugin.install.ce
                    inputs: {}
        """

        result = self.parse(yaml)
        operations = set()
        for op in result['nodes'][0]['operations']:
            if op.startswith('op_'):
                operations.add(op)

        result_operations = result['nodes'][0]['operations']
        self.assertEqual(5, len(operations))
        self.assertEqual('install.ba', result_operations['op_a']['operation'])
        self.assertEqual('install.cb', result_operations['op_b']['operation'])
        self.assertEqual('install.ac', result_operations['op_c']['operation'])
        self.assertEqual('install.bd', result_operations['op_d']['operation'])
        self.assertEqual('install.ce', result_operations['op_e']['operation'])


class InterfacesMergerTest(AbstractTestParser, TempDirectoryTestCase):

    def test_merge_interfaces(self):

        imported_yaml = """
node_types:
    type_a:
        interfaces:
            interface_a:
                op_aa:
                    implementation: test_plugin.install.aa
                    inputs: {}
            interface_b:
                op_ab:
                    implementation: test_plugin.install.ab
                    inputs: {}
            interface_c:
                op_ac:
                    implementation: test_plugin.install.ac
                    inputs: {}
        """

        yaml = self.create_yaml_with_imports([imported_yaml]) + self.BASIC_PLUGIN + """
node_types:
    type_b:
        derived_from: type_a
        interfaces:
            interface_a:
                op_ba:
                    implementation: test_plugin.install.ba
                    inputs: {}
            interface_d:
                op_bd:
                    implementation: test_plugin.install.bd
                    inputs: {}
node_templates:
    template_c:
        type: type_b
        interfaces:
            interface_b:
                op_cb:
                    implementation: test_plugin.install.cb
                    inputs: {}
            interface_e:
                op_ce:
                    implementation: test_plugin.install.ce
                    inputs: {}
        """

        result = self.parse(yaml)
        operations = set()
        for op in result['nodes'][0]['operations']:
            if op.startswith('interface_'):
                operations.add(op[:op.index('.')])

        result_operations = result['nodes'][0]['operations']
        self.assertEqual(5, len(operations))
        self.assertIsNotNone(result_operations['interface_a.op_aa'])
        self.assertIsNotNone(result_operations['interface_a.op_ba'])
        self.assertIsNotNone(result_operations['interface_b.op_ab'])
        self.assertIsNotNone(result_operations['interface_b.op_cb'])
        self.assertEqual('install.aa', result_operations['interface_a.op_aa']['operation'])
        self.assertEqual('install.ba', result_operations['interface_a.op_ba']['operation'])
        self.assertEqual('install.ab', result_operations['interface_b.op_ab']['operation'])
        self.assertEqual('install.cb', result_operations['interface_b.op_cb']['operation'])
        self.assertEqual('install.ac', result_operations['interface_c.op_ac']['operation'])
        self.assertEqual('install.bd', result_operations['interface_d.op_bd']['operation'])
        self.assertEqual('install.ce', result_operations['interface_e.op_ce']['operation'])


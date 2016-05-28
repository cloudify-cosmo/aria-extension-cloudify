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

from aria.exceptions import MissingRequiredInputError, UnknownInputError

from ..suite import PrepareDeploymentPlanTestCase


class TestInputs(PrepareDeploymentPlanTestCase):
    def test_inputs_provided_to_plan(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 9000
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
    """
        parsed = self.prepare_deployment_plan(
            deployment_kwargs={'inputs': {'port': 8000}})
        self.assertEqual(8000, parsed['nodes'][0]['properties']['port'])

    def test_missing_input(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port: {}
    name_i: {}
node_types:
    webserver_type:
        properties:
            port: {}
            name: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
            name: { get_input: name_i }
    """
        self.assert_prepare_deployment_raise_exception(
            exception_types=MissingRequiredInputError,
            extra_tests=[
                lambda exc: self.assertTrue('name_i' in str(exc).split('-')[0])
            ],
            deployment_kwargs={'inputs': {'port': '8080'}},
        )

        self.assert_prepare_deployment_raise_exception(
            exception_types=MissingRequiredInputError,
            extra_tests=[
                lambda exc: self.assertTrue('name_i' in str(exc).split('-')[0]),
                lambda exc: self.assertTrue('port' in str(exc).split('-')[0])
            ],
        )

        self.assert_prepare_deployment_raise_exception(
            exception_types=MissingRequiredInputError,
            extra_tests=[
                lambda exc: self.assertTrue('name_i' in str(exc).split('-')[0]),
                lambda exc: self.assertTrue('port' in str(exc).split('-')[0]),
            ],
            deployment_kwargs={'inputs': {}},
        )

    def test_inputs_default_value(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""
        parsed = self.prepare_deployment_plan()
        self.assertEqual(8080, parsed['nodes'][0]['properties']['port'])

    def test_unknown_input_provided(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: port }
"""

        self.assert_prepare_deployment_raise_exception(
            exception_types=UnknownInputError,
            extra_tests=[
                lambda exc: self.assertTrue('unknown_input_1' in str(exc).split('-')[0]),
            ],
            deployment_kwargs={'inputs': {'unknown_input_1': 'a'}},
        )
        self.assert_prepare_deployment_raise_exception(
            exception_types=UnknownInputError,
            extra_tests=[
                lambda exc: self.assertTrue('unknown_input_1' in str(exc)),
                lambda exc: self.assertTrue('unknown_input_2' in str(exc)),
            ],
            deployment_kwargs={'inputs': {'unknown_input_1': 'a', 'unknown_input_2': 'b'}},
        )

    def test_get_input_in_nested_property(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                port: { get_input: port }
"""
        parsed = self.prepare_deployment_plan()
        self.assertEqual(8080, parsed['nodes'][0]['properties']['server']['port'])
        self.template.clear()
        self.template.version_section('1.0')
        self.template.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                port: { get_input: port }
                some_prop: { get_input: unknown }
"""
        self.assertRaises(
            UnknownInputError,
            self.parse,
            str(self.template))

    def test_get_input_list_property(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                - item1
                - port: { get_input: port }
"""
        parsed = self.prepare_deployment_plan()
        self.assertEqual(8080, parsed['nodes'][0]['properties']['server'][1]['port'])
        self.template.clear()
        self.template.version_section('1.0')
        self.template.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties:
            server: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            server:
                - item1
                - port: { get_input: port1122 }
"""
        self.assertRaises(UnknownInputError, self.parse, str(self.template))

    def test_input_in_interface(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    plugin:
        source: dummy
inputs:
    port:
        default: 8080
node_types:
    webserver_type: {}
relationships:
    tosca.relationships.HostedOn: {}
    rel:
        derived_from: tosca.relationships.HostedOn
        source_interfaces:
            source_interface:
                op1:
                    implementation: plugin.operation
                    inputs:
                        source_port:
                            default: { get_input: port }
        target_interfaces:
            target_interface:
                op2:
                    implementation: plugin.operation
                    inputs:
                        target_port:
                            default: { get_input: port }
node_templates:
    ws1:
        type: webserver_type
    webserver:
        type: webserver_type
        interfaces:
            lifecycle:
                configure:
                    implementation: plugin.operation
                    inputs:
                        port: { get_input: port }
        relationships:
            -   type: rel
                target: ws1
"""
        prepared = self.prepare_deployment_plan()

        node_template = [
            x for x in prepared['nodes']
            if x['name'] == 'webserver'][0]
        op = node_template['operations']['lifecycle.configure']
        self.assertEqual(8080, op['inputs']['port'])
        op = node_template['operations']['configure']
        self.assertEqual(8080, op['inputs']['port'])
        # relationship interfaces
        source_ops = node_template['relationships'][0]['source_operations']
        self.assertEqual(8080, source_ops['source_interface.op1']['inputs']['source_port'])
        self.assertEqual(8080, source_ops['op1']['inputs']['source_port'])
        target_ops = node_template['relationships'][0]['target_operations']
        self.assertEqual(
            8080,
            target_ops['target_interface.op2']['inputs']['target_port'])
        self.assertEqual(8080, target_ops['op2']['inputs']['target_port'])

        prepared = self.prepare_deployment_plan(
            deployment_kwargs={'inputs': {'port': 8000}})
        node_template = [
            x for x in prepared['nodes']
            if x['name'] == 'webserver'][0]
        op = node_template['operations']['lifecycle.configure']
        self.assertEqual(8000, op['inputs']['port'])
        op = node_template['operations']['configure']
        self.assertEqual(8000, op['inputs']['port'])
        # relationship interfaces
        source_ops = node_template['relationships'][0]['source_operations']
        self.assertEqual(
            8000,
            source_ops['source_interface.op1']['inputs']['source_port'])
        self.assertEqual(8000, source_ops['op1']['inputs']['source_port'])
        target_ops = node_template['relationships'][0]['target_operations']
        self.assertEqual(
            8000,
            target_ops['target_interface.op2']['inputs']['target_port'])
        self.assertEqual(8000, target_ops['op2']['inputs']['target_port'])

    def test_input_in_outputs(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        default: 8080
node_types:
    webserver_type:
        properties: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    a:
        value: { get_input: port }
"""
        prepared = self.prepare_deployment_plan()
        outputs = prepared.outputs
        self.assertEqual(8080, outputs['a']['value'])

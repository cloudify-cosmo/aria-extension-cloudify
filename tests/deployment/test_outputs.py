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

from aria.parser.framework import functions

from ..suite import PrepareDeploymentPlanTestCase
from ..parser.test_outputs import NodeInstance, Node


class TestOutputs(PrepareDeploymentPlanTestCase):
    def test_outputs_valid_output(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port0:
        description: p0
        value: 1234
    port1:
        description: p1
        value: some_port
    port2:
        description: p2
        value: {}
    port3:
        description: p3
        value: []
    port4:
        description: p4
        value: false
    """
        parsed = self.parse()
        outputs = parsed['outputs']
        self.assertEqual(5, len(parsed['outputs']))
        self.assertEqual('p0', outputs['port0']['description'])
        self.assertEqual(1234, outputs['port0']['value'])
        self.assertEqual('p1', outputs['port1']['description'])
        self.assertEqual('some_port', outputs['port1']['value'])
        self.assertEqual('p2', outputs['port2']['description'])
        self.assertEqual({}, outputs['port2']['value'])
        self.assertEqual('p3', outputs['port3']['description'])
        self.assertEqual([], outputs['port3']['value'])
        self.assertEqual('p4', outputs['port4']['description'])
        self.assertFalse(outputs['port4']['value'])
        prepared = self.prepare_deployment_plan()
        self.assertEqual(parsed['outputs'], prepared['outputs'])

    def test_valid_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        parsed = self.parse()
        outputs = parsed['outputs']
        func = functions.parse(outputs['port']['value'])
        self.assertTrue(isinstance(func, functions.GetAttribute))
        self.assertEqual('webserver', func.node_name)
        self.assertEqual('port', func.attribute_path[0])
        prepared = self.prepare_deployment_plan()
        self.assertEqual(parsed['outputs'], prepared['outputs'])

    def test_valid_evaluation(self):
        self.template.version_section('1.1')
        self.template += """
inputs:
    input:
        default: input_value
node_types:
    webserver_type:
        properties:
            property:
                default: property_value
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
    endpoint:
        value:
            port: { get_attribute: [ webserver, port ] }
    concatenated:
        value: { concat: [one,
                          {get_property: [webserver, property]},
                          {get_attribute: [webserver, attribute]},
                          {get_input: input},
                          five] }
"""
        parsed = self.prepare_deployment_plan()
        concatenated = parsed['outputs']['concatenated']['value']['concat']
        self.assertEqual('one', concatenated[0])
        self.assertEqual('property_value', concatenated[1])
        self.assertEqual({'get_attribute': ['webserver', 'attribute']}, concatenated[2])
        self.assertEqual('input_value', concatenated[3])
        self.assertEqual('five', concatenated[4])

        def get_node_instances(node_id=None):
            return [
                NodeInstance({
                    'id': 'webserver1',
                    'node_id': 'webserver',
                    'runtime_properties': {
                        'port': 8080,
                        'attribute': 'attribute_value',
                    }})
            ]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node(id=node_id)

        o = functions.evaluate_outputs(
            parsed['outputs'],
            get_node_instances,
            get_node_instance,
            get_node)
        self.assertEqual(8080, o['port'])
        self.assertEqual(8080, o['endpoint']['port'])
        self.assertEqual(
            'oneproperty_valueattribute_valueinput_valuefive',
            o['concatenated'])

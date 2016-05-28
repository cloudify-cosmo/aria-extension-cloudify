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

from aria.parser.exceptions import (
    DSLParsingFormatException, FunctionEvaluationError,
)
from aria.parser.framework.functions import evaluate_outputs

from ..suite import ParserTestCase


class TestOutputs(ParserTestCase):
    def test_outputs_definition(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs: {}
"""
        parsed = self.parse()
        self.assertEqual(0, len(parsed['outputs']))

    def test_invalid_outputs(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
"""
        self.assertRaises(DSLParsingFormatException, self.parse)

    def test_invalid_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: [ webserver, port ] }
"""
        try:
            self.parse()
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))

        self.template.clear()
        self.template.version_section('1.0')
        self.template += """
node_templates: {}
outputs:
    port:
        description: p0
        value: { get_attribute: aaa }
"""
        try:
            self.parse()
            self.fail('Expected exception.')
        except ValueError, e:
            self.assertTrue('Illegal arguments passed' in str(e))

    def test_invalid_nested_get_attribute(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    endpoint:
        description: p0
        value:
            ip: 10.0.0.1
            port: { get_attribute: [ aaa, port ] }
"""
        try:
            self.parse()
            self.fail('Expected exception.')
        except KeyError, e:
            self.assertTrue('does not exist' in str(e))

    def test_unknown_node_instance_evaluation(self):
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

        def get_node_instances(node_id=None):
            return []

        try:
            evaluate_outputs(parsed['outputs'],
                             get_node_instances,
                             None, None)
            self.fail()
        except FunctionEvaluationError, e:
            self.assertIn('Node specified in function does not exist', str(e))
            self.assertIn('webserver', str(e))

    def test_invalid_multi_instance_evaluation(self):
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

        def get_node_instances(node_id=None):
            node_instance = NodeInstance({
                'id': 'webserver1',
                'node_id': 'webserver',
                'runtime_properties': {'port': 8080},
            })
            return [node_instance, node_instance]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        try:
            evaluate_outputs(parsed['outputs'],
                             get_node_instances,
                             get_node_instance,
                             get_node)
            self.fail()
        except FunctionEvaluationError, e:
            self.assertIn('unambiguously', str(e))
            self.assertIn('webserver', str(e))

    def test_get_attribute_nested_property(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
outputs:
    port:
        value: { get_attribute: [ webserver, endpoint, port ] }
    protocol:
        value: { get_attribute: [ webserver, endpoint, url, protocol ] }
    none:
        value: { get_attribute: [ webserver, endpoint, url, none ] }
"""
        parsed = self.parse()

        def get_node_instances(node_id=None):
            node_instance = NodeInstance({
                'id': 'webserver1',
                'node_id': 'webserver',
                'runtime_properties': {
                    'endpoint': {
                        'url': {'protocol': 'http'},
                        'port': 8080,
                    }}})
            return [node_instance]

        def get_node_instance(node_instance_id):
            return get_node_instances()[0]

        def get_node(node_id):
            return Node({'id': node_id})

        outputs = evaluate_outputs(parsed['outputs'],
                                   get_node_instances,
                                   get_node_instance,
                                   get_node)
        self.assertEqual(8080, outputs['port'])
        self.assertEqual('http', outputs['protocol'])
        self.assertIsNone(outputs['none'])


class NodeInstance(dict):
    @property
    def id(self):
        return self.get('id')

    @property
    def node_id(self):
        return self.get('node_id')

    @property
    def runtime_properties(self):
        return self.get('runtime_properties')


class Node(dict):
    @property
    def id(self):
        return self.get('id')

    @property
    def properties(self):
        return self.get('properties', {})

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

from aria.parser.exceptions import UnknownInputError, DSLParsingLogicException

from ..suite import ParserTestCase


class TestInputs(ParserTestCase):
    def test_inputs_definition(self):
        self.template.version_section('1.0')
        self.template += """
inputs: {}
node_templates: {}
"""
        parsed = self.parse()
        self.assertEqual(0, len(parsed['inputs']))

    def test_input_definition(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        description: the port
        default: 8080
node_templates: {}
"""
        parsed = self.parse()
        self.assertEqual(1, len(parsed['inputs']))
        self.assertEqual(8080, parsed['inputs']['port']['default'])
        self.assertEqual('the port', parsed['inputs']['port']['description'])

    def test_two_inputs(self):
        self.template.version_section('1.0')
        self.template += """
inputs:
    port:
        description: the port
        default: 8080
    ip: {}
node_templates: {}
"""
        parsed = self.parse()
        self.assertEqual(2, len(parsed['inputs']))
        self.assertEqual(8080, parsed['inputs']['port']['default'])
        self.assertEqual('the port', parsed['inputs']['port']['description'])
        self.assertEqual(0, len(parsed['inputs']['ip']))

    def test_verify_get_input_in_properties(self):
        self.template.version_section('1.0')
        self.template += """
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
        self.assertRaises(UnknownInputError, self.parse)
        self.template.clear()
        self.template.version_section('1.0')
        self.template.template += """
node_types:
    webserver_type:
        properties:
            port: {}
node_templates:
    webserver:
        type: webserver_type
        properties:
            port: { get_input: {} }
"""
        self.assertRaises(ValueError, self.parse)
        self.template.clear()
        self.template.version_section('1.0')
        self.template.template += """
inputs:
    port: {}
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
        self.parse()

    def test_invalid_input_in_interfaces(self):
        self.template.version_section('1.0')
        self.template += """
plugins:
    plugin:
        source: dummy
node_types:
    webserver_type: {}
node_templates:
    webserver:
        type: webserver_type
        interfaces:
            lifecycle:
                configure:
                    implementation: plugin.operation
                    inputs:
                        port: { get_input: aaa }
"""
        self.assertRaises(UnknownInputError, self.parse)

    def test_missing_input_exception(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
  type:
    interfaces:
      interface:
        op:
          implementation: plugin.mapping
          inputs:
            some_input:
              type: string
node_templates:
  node:
    type: type
plugins:
  plugin:
    install: false
"""
        self.assert_parser_raise_exception(
            error_code=107,
            exception_types=DSLParsingLogicException,
            extra_tests=[
                lambda exc: self.assertIn('some_input', str(exc))])

    def test_missing_inputs_both_reported(self):
        self.template.version_section('1.0')
        self.template += """
node_types:
  type:
    interfaces:
      interface:
        op:
          implementation: plugin.mapping
          inputs:
            some_input:
              type: string
            another_input:
              type: string
node_templates:
  node:
    type: type
plugins:
  plugin:
    install: false
"""
        self.assert_parser_raise_exception(
            error_code=107,
            exception_types=DSLParsingLogicException,
            extra_tests=[
                lambda exc: self.assertIn('some_input', str(exc)),
                lambda exc: self.assertIn('another_input', str(exc)),
            ])

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

from aria.utils import yaml_dumps, yaml_loads

from .suite import ParserTestCase, CloudifyParserError


class PluginsTest(ParserTestCase):
    def test_plugin_with_install_true_existing_source(self):
        self._test(install=True, source='dummy')

    def test_plugin_with_install_true_existing_package_name(self):
        self._test(install=True, package_name='package')

    def test_plugin_with_install_false_existing_source(self):
        self._test(install=False, source='dummy')

    def test_plugin_with_install_false_existing_package_name(self):
        self._test(install=False, package_name='package')

    def test_plugin_with_install_false_missing_source_and_package(self):
        self._test(install=False)

    def test_plugin_with_missing_install_existing_source(self):
        self._test(source='dummy')

    def test_plugin_with_missing_install_existing_package(self):
        self._test(package_name='package')

    def test_plugin_with_missing_install_missing_source_and_package(self):
        self._test(partial_issue_message='plugin "test_plugin" is set to '
                                         'install but does not have "source" '
                                         'or "package_name"')
        # TODO issue #1 in test_plugins

    def test_plugin_with_install_true_missing_source_and_package(self):
        self._test(install=True,
                   partial_issue_message='plugin "test_plugin" is set to '
                                         'install but does not have "source" '
                                         'or "package_name"')
        # TODO issue #2 in test_plugins

    def _test(self,
              install=None,
              source=None,
              package_name=None,
              partial_issue_message=None):
        raw_parsed_yaml = yaml_loads("""
plugins:
  test_plugin: {}

node_templates:
  test_node:
    type: type
    interfaces:
      test_interface1:
        install: test_plugin.install

node_types:
  type: {}
""")
        plugin = {
            'executor': 'central_deployment_agent'
        }
        if install is not None:
            plugin['install'] = install
        if source is not None:
            plugin['source'] = source
        if package_name is not None:
            plugin['package_name'] = package_name

        raw_parsed_yaml['plugins']['test_plugin'] = plugin
        self.template.version_section('cloudify_dsl', '1.2')
        self.template += yaml_dumps(raw_parsed_yaml)
        if partial_issue_message:
            ex = self.assertRaises(CloudifyParserError, self.parse)
            self.assertIn(partial_issue_message,
                          ex.message)

        else:
            result = self.parse()
            plugin = result['nodes'][0]['plugins'][0]
            if install is not None:
                self.assertEqual(install, plugin['install'])
            if source is not None:
                self.assertEqual(source, plugin['source'])
            if package_name is not None:
                self.assertEqual(package_name, plugin['package_name'])

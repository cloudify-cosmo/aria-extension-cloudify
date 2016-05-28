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

from ..suite import PrepareDeploymentPlanTestCase


class TestGetAttribute(PrepareDeploymentPlanTestCase):
    def test_has_intrinsic_functions_property(self):
        self.template.version_section('1.0')
        self.template += """
relationships:
    tosca.relationships.HostedOn: {}
plugins:
    p:
        install: false
node_types:
    webserver_type: {}
node_templates:
    node:
        type: webserver_type
    webserver:
        type: webserver_type
        interfaces:
            test:
                op_with_no_get_attribute:
                    implementation: p.p
                    inputs:
                        a: 1
                op_with_get_attribute:
                    implementation: p.p
                    inputs:
                        a: { get_attribute: [SELF, a] }
        relationships:
            -   type: tosca.relationships.HostedOn
                target: node
                source_interfaces:
                    test:
                        op_with_no_get_attribute:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_attribute:
                            implementation: p.p
                            inputs:
                                a: { get_attribute: [SOURCE, a] }
                target_interfaces:
                    test:
                        op_with_no_get_attribute:
                            implementation: p.p
                            inputs:
                                a: 1
                        op_with_get_attribute:
                            implementation: p.p
                            inputs:
                                a: { get_attribute: [TARGET, a] }
"""
        parsed = self.prepare_deployment_plan()

        for node in parsed.node_templates:
            if node['id'] == 'webserver':
                webserver_node = node
                break
        else:
            self.fail('did not find web-server node')

        self._assertion(webserver_node['operations'])
        self._assertion(webserver_node['relationships'][0]['source_operations'])
        self._assertion(webserver_node['relationships'][0]['target_operations'])

    def _assertion(self, operations):
        op = operations['test.op_with_no_get_attribute']
        self.assertIs(False, op.get('has_intrinsic_functions'))
        op = operations['test.op_with_get_attribute']
        self.assertIs(True, op.get('has_intrinsic_functions'))

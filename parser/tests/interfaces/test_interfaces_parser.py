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

from ..framework.abstract_test_parser import AbstractTestParser
import yaml


class InterfacesParserTest(AbstractTestParser):

    @staticmethod
    def _expanded_node_operation(operation):
        return {
            'operation': operation.get('operation') or '',
            'max_retries': None,
            'retry_interval': None,
            'has_intrinsic_functions': False,
            'plugin': operation.get('plugin') or None,
            'inputs': operation.get('inputs') or {},
            'executor': operation.get('executor') or None
        }

    @staticmethod
    def _expanded_relationship_operation(operation):
        return {
            'implementation': operation.get('implementation') or '',
            'max_retries': None,
            'retry_interval': None,
            'inputs': operation.get('inputs') or {},
            'executor': operation.get('executor') or None
        }

    def _assert_merged_node_interfaces(self,
                                       merged_interfaces,
                                       expected_merged_interfaces):

        for operation_name, operation in expected_merged_interfaces.iteritems():

            expected_merged_interfaces[operation_name].update(
                self._expanded_node_operation(operation))

        merged_interfaces = {op: merged_interfaces[op] for op in merged_interfaces if '.' in op}

        self.assertEqual(expected_merged_interfaces, merged_interfaces)

    def _assert_merged_relationship_interfaces(self,
                                               merged_interfaces,
                                               expected_merged_interfaces):
        for interface_name in expected_merged_interfaces:
            for operation_name, operation in expected_merged_interfaces[interface_name].iteritems():
                expected_merged_interfaces[interface_name][operation_name].update(
                    self._expanded_relationship_operation(operation))

        self.assertEqual(expected_merged_interfaces, merged_interfaces)

    def _merge_interfaces(self,
                          node_type_interfaces=None,
                          derived_node_type_interfaces=None,
                          node_template_interfaces=None,
                          relationship_type_interfaces=None,
                          derived_relationship_type_interfaces=None,
                          relationship_template_interfaces=None):

        blueprint_dict = {
            'tosca_definitions_version': 'cloudify_dsl_1_3',
            'node_types': {
                'node_type': {
                    'interfaces': node_type_interfaces or {}
                },
                'derived_node_type': {
                    'derived_from': 'node_type',
                    'interfaces': derived_node_type_interfaces or {}
                }
            },
            'node_templates': {
                'node1': {
                    'type': 'node_type',
                    'interfaces': node_template_interfaces or {},
                    'relationships': [{
                         'type': 'relationship_type',
                         'target': 'node2',
                         'source_interfaces': relationship_template_interfaces or {}
                    }]},
                'node2': {  # only here to be the target of node1's relationship
                    'type': 'node_type',
                }
            },
            'relationships': {
                'relationship_type': {
                    'source_interfaces': relationship_type_interfaces or {}
                },
                'derived_relationship_type': {
                    'derived_from': 'relationship_type',
                    'source_interfaces': derived_relationship_type_interfaces or {}
                },
            },
            'plugins': {
                'mock': {
                    'source': 'path',
                    'executor': 'central_deployment_agent'
                }
            }
        }
        blueprint_yaml = yaml.dump(blueprint_dict)
        parsed = self.parse(blueprint_yaml)

        if node_type_interfaces is not None:
            if derived_node_type_interfaces is not None:
                # TODO return the derived node type's interfaces
                pass
            else:
                return parsed['nodes'][0]['operations']
        if relationship_type_interfaces is not None:
            if derived_relationship_type_interfaces is not None:
                return parsed['relationships']['derived_relationship_type']['source_interfaces']
            else:
                # TODO return the relationship templates's interfaces
                return parsed['nodes'][0]['relationships'][0]['source_interfaces']
                pass

    # TODO waiting for information about node_type interfaces to be stored in a ConsumptionContext
    def test_merge_node_type_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }}

        derived_node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        expected_merged_interfaces = {
            'interface1.start': {
                'plugin': 'mock',
                'operation': 'tasks.start',
                'executor': 'central_deployment_agent',
            },
            'interface1.stop': {
                'plugin': 'mock',
                'operation': 'tasks.stop',
                'inputs': {
                    'key': {
                        'default': 'value'
                    }
                },
                'executor': 'central_deployment_agent',
            },
            'interface2.start': {}
        }
        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            derived_node_type_interfaces=derived_node_type_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    # TODO waiting for information about node_type interfaces to be stored in a ConsumptionContext
    def test_merge_node_type_interfaces_no_interfaces_on_overriding(self):

        node_type_interfaces = {}

        derived_node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }}

        expected_merged_interfaces = {
            'interface1.start': {},
            'interface1.stop': {},
            'interface2.start': {}
        }
        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            derived_node_type_interfaces=derived_node_type_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    # TODO waiting for information about node_type interfaces to be stored in a ConsumptionContext
    def test_merge_node_type_interfaces_no_interfaces_on_overridden(self):

        node_type_interfaces = {}

        derived_node_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {

            'interface1.start': {},
            'interface1.stop': {},
            'interface2.start': {}
        }
        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            derived_node_type_interfaces=derived_node_type_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    def test_merge_node_type_and_node_template_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start-overridden',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            },
            'interface1.stop': {
                'operation': 'tasks.stop',
                'plugin': 'mock',
                'executor': 'central_deployment_agent',
                'inputs': {
                    'key': 'value'
                }}}

        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            node_template_interfaces=node_template_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    def test_merge_node_type_no_interfaces_and_node_template_interfaces(self):

        node_type_interfaces = {}

        node_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start'
            }
        }

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            }
        }

        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            node_template_interfaces=node_template_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    def test_merge_node_type_interfaces_and_node_template_no_interfaces(self):

        node_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                }
            }
        }
        node_template_interfaces = {}

        expected_merged_interfaces = {
            'interface1.start': {
                'operation': 'tasks.start',
                'plugin': 'mock',
                'executor': 'central_deployment_agent'
            }
        }

        merged_interfaces = self._merge_interfaces(
            node_type_interfaces=node_type_interfaces,
            node_template_interfaces=node_template_interfaces)

        self._assert_merged_node_interfaces(merged_interfaces,
                                            expected_merged_interfaces)

    def test_merge_relationship_type_interfaces(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        derived_relationship_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        expected_merged_interfaces = {

                'interface1': {
                    'start': {
                        'operation': 'tasks.start',
                        'executor': 'central_deployment_agent',
                        'plugin': 'mock'
                    },
                    'stop': {
                        'operation': 'tasks.stop',
                        'executor': 'central_deployment_agent',
                        'plugin': 'mock',
                        'inputs': {
                            'key': {
                                'default': 'value'
                            }}}},
                'interface2': {
                    'start': {}
                }
            }

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            derived_relationship_type_interfaces=derived_relationship_type_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overriding(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }
        derived_relationship_type_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            derived_relationship_type_interfaces=derived_relationship_type_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

    def test_merge_relationship_type_interfaces_no_interfaces_on_overridden(self):

        relationship_type_interfaces = {}

        derived_relationship_type_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {},
                'stop': {}
            },
            'interface2': {
                'start': {}
            }
        }

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            derived_relationship_type_interfaces=derived_relationship_type_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_interfaces(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        relationship_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }}

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'executor': 'central_deployment_agent'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'executor': 'central_deployment_agent',
                    'inputs': {
                        'key': 'value'
                    }
                }}}

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            relationship_template_interfaces=relationship_template_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

    def test_merge_relationship_type_no_interfaces_and_instance_interfaces(self):

        relationship_type_interfaces = {}
        relationship_template_interfaces = {
            'interface1': {
                'start': 'mock.tasks.start-overridden'
            }
        }

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start-overridden',
                    'executor': 'central_deployment_agent'
                }}}

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            relationship_template_interfaces=relationship_template_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

    def test_merge_relationship_type_and_instance_no_interfaces(self):

        relationship_type_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'inputs': {
                        'key': {
                            'default': 'value'
                        }}}}}

        relationship_template_interfaces = {}

        expected_merged_interfaces = {
            'interface1': {
                'start': {
                    'implementation': 'mock.tasks.start',
                    'executor': 'central_deployment_agent'
                },
                'stop': {
                    'implementation': 'mock.tasks.stop',
                    'executor': 'central_deployment_agent',
                    'inputs': {
                        'key': 'value'
                    }}}}

        merged_interfaces = self._merge_interfaces(
            relationship_type_interfaces=relationship_type_interfaces,
            relationship_template_interfaces=relationship_template_interfaces)

        self._assert_merged_relationship_interfaces(merged_interfaces,
                                                    expected_merged_interfaces)

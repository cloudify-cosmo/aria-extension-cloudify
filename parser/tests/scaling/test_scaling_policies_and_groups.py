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

from dsl_parser.constants import UNBOUNDED, UNBOUNDED_LITERAL, SCALING_POLICY

from ..suite import ParserTestCase


class TestScalingPoliciesAndGroups(ParserTestCase):
    def test_scaling_policy_and_group_default_properties(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1,
        }
        # TODO issue #1 in test_scaling_policies_and_groups
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_empty_properties(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
            'properties': {},
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1,
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_groups_default_instances(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'default_instances': 3,
            },
        }
        expected = {
            'default_instances': 3,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': 3,
            'planned_instances': 3
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_max_instances(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'max_instances': 3,
            },
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': 3,
            'current_instances': 1,
            'planned_instances': 1,
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_min_instances(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'min_instances': 0,
            },
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1,
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def test_scaling_policy_and_group_unbounded_literal(self):
        policy = {
            'type': SCALING_POLICY,
            'targets': ['group'],
            'properties': {
                'max_instances': UNBOUNDED_LITERAL,
            },
        }
        expected = {
            'default_instances': 1,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': 1,
            'planned_instances': 1,
        }
        self.assert_scaling_policy_and_group(policy=policy, expected=expected)

    def assert_scaling_policy_and_group(self, policy, expected):
        self.template.from_members(
            groups={'group': ['node']},
            nodes={'node': None},
            policies={'policy': policy})
        plan = self.parse()
        self.assertEqual(
            expected,
            plan['policies']['policy']['properties'])
        self.assertEqual(
            expected,
            plan['scaling_groups']['group']['properties'])


class TestScalingPoliciesAndGroupsExtra(ParserTestCase):
    def test_group_as_group_member(self):
        self.template.from_members(
            nodes={'node': None},
            groups={
                'group': ['node'],
                'group2': ['group'],
            },
        )
        plan = self.parse()
        self.assertEqual(['node'], plan['groups']['group']['members'])
        self.assertEqual(['group'], plan['groups']['group2']['members'])


class TestRemovedContainedInMember(ParserTestCase):
    def test_removed_contained_in_member1(self):
        groups = {
            'group': ['node1', 'node2'],
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
        }
        expected = {
            'group': ['node1'],
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member2(self):
        groups = {
            'group1': ['node1', 'group2'],
            'group2': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
        }
        expected = {
            'group1': ['node1'],
            'group2': ['node2']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member3(self):
        groups = {
            'group': ['node1', 'node3'],
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node2'
        }
        expected = {
            'group': ['node1']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member4(self):
        groups = {
            'group': ['node1', 'group2'],
            'group2': ['group3'],
            'group3': ['node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node2'
        }
        expected = {
            'group': ['node1'],
            'group2': ['group3'],
            'group3': ['node3']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member5(self):
        groups = {
            'group': ['group2'],
            'group2': ['node1', 'node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
        }
        expected = {
            'group': ['group2'],
            'group2': ['node1']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member6(self):
        groups = {
            'group1': ['group2', 'group3', 'node4'],
            'group2': ['node1'],
            'group3': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node1',
            'node4': None
        }
        expected = {
            'group1': ['group2', 'node4'],###
            'group2': ['node1'],
            'group3': ['node2', 'node3']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member7(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node1', 'node2', 'node3', 'group3'],
            'group3': ['node4']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None,
            'node4': None
        }
        expected = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3'],
            'group3': ['node4']
        }
        self.assert_removal(groups, nodes, expected)

    def test_removed_contained_in_member8(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3', 'group4'],
            'group3': ['node4'],
            'group4': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None,
            'node4': None
        }
        expected = {
            'group1': ['group2'],
            'group2': ['node1', 'node3', 'group3'],
            'group3': ['node4'],
            'group4': ['node2']
        }
        self.assert_removal(groups, nodes, expected)

    def assert_removal(self, groups, nodes, expected):

        self.template.from_members(
            groups=groups,
            nodes=nodes,
            policies={'policy': {'type': SCALING_POLICY, 'targets': groups.keys()}})
        plan = self.parse()
        for group, expected_members in expected.iteritems():
            self.assertEqual(
                set(expected_members),
                set(plan['scaling_groups'][group]['members']))


class TestScalingPoliciesAndGroupsValidation(ParserTestCase):
    def test_missing_policy_type(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'targets': ['group']
            }
        }
        self.assert_validation(
            expected_issue_messages=[
                'required field "type" in '
                '"aria_extension_cloudify.v1_3.templates.PolicyTemplate" '
                'does not have a value'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_non_scaling_policy_type(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': 'some_policy',
                'targets': ['group']
            }
        }
        self.assert_validation(
            expected_issue_messages=[
                '"type" refers to an unknown policy type in "policy": u\'some_policy\''],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_non_group_target(self):
        nodes = {'node': None}
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['node']
            }
        }
        self.assert_validation(
            expected_issue_messages=[
                '"targets" refers to an unknown group in "policy": [u\'node\']'],
            policies=policies,
            nodes=nodes)

    def test_no_targets(self):
        policies = {
            'policy': {
                'type': SCALING_POLICY
            }
        }
        self.assert_validation(
            expected_issue_messages=[
                'required field "targets" in '
                '"aria_extension_cloudify.v1_3.templates.PolicyTemplate" '
                'does not have a value'],
            policies=policies)

    def test_empty_targets(self):
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': []
            }
        }
        self.assert_validation(
            expected_issue_messages=[''],
            policies=policies)

    def test_invalid_min_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'min_instances': -1
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"min_instances" is not a positive integer or zero'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_max_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'max_instances': 0
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"default_instances" is greater than "max_instances"'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_max_instances_string_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'max_instances': 'illegal_value'
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['invalid literal for int() '
                                     'with base 10: \'illegal_value\''],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_invalid_default_instances_value(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': -1
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"default_instances" is not a positive integer or zero'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_min_instances_greater_than_max_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'min_instances': 5,
                    'max_instances': 1,
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"max_instances" is lesser than "min_instances"'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_default_instances_greater_than_max_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': 5,
                    'max_instances': 4,
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"default_instances" is greater than "max_instances"'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_default_instances_smaller_than_min_instances(self):
        nodes = {'node': None}
        groups = {
            'group': ['node']
        }
        policies = {
            'policy': {
                'type': SCALING_POLICY,
                'targets': ['group'],
                'properties': {
                    'default_instances': 2,
                    'min_instances': 4,
                }
            }
        }
        self.assert_validation(
            expected_issue_messages=['"default_instances" is lesser than "min_instances"'],
            groups=groups,
            nodes=nodes,
            policies=policies)

    def test_validate_no_group_cycles1(self):
        groups = {
            'group1': ['group2'],
            'group2': ['group1']
        }
        self.assert_validation(
            expected_issue_messages=['maximum recursion depth '
                                     'exceeded while calling a Python object'],
            groups=groups)

    def test_validate_no_group_cycles2(self):
        groups = {
            'group1': ['group2'],
            'group2': ['group3'],
            'group3': ['group4'],
            'group4': ['group1'],
        }
        self.assert_validation(
            expected_issue_messages=['maximum recursion depth '
                                     'exceeded while calling a Python object'],
            groups=groups)

    def test_validate_node_type_group_members_in_one_group_only(self):
        groups = {
            'group1': ['node'],
            'group2': ['node']
        }
        nodes = {
            'node': None
        }
        self.assert_validation(
            expected_issue_messages=[''],
            groups=groups,
            nodes=nodes)

    def test_validate_group_type_group_members_in_one_group_only(self):
        groups = {
            'group1': ['node'],
            'group2': ['group1'],
            'group3': ['group1']
        }
        nodes = {
            'node': None
        }
        self.assert_validation(
            expected_issue_messages=[''],
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members1(self):
        groups = {
            'group': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None
        }
        self.assert_validation(
            expected_issue_messages=[''],
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members2(self):
        groups = {
            'group1': ['group2'],
            'group2': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': None
        }
        self.assert_validation(
            expected_issue_messages=[''],
            groups=groups,
            nodes=nodes)

    def test_validate_non_contained_group_members3(self):
        groups = {
            'group1': ['node4', 'group2'],
            'group2': ['node2', 'node3']
        }
        nodes = {
            'node1': None,
            'node2': 'node1',
            'node3': 'node1',
            'node4': None
        }
        self.assert_validation(
            expected_issue_messages=[''],
            groups=groups,
            nodes=nodes)

    def test_validate_illegal_instances_dict_value(self):
        nodes = {
            'node': None
        }
        groups = {
            'group': ['node']
        }
        for instances in ['default', 'min', 'max']:
            policies = {
                'policy': {
                    'type': SCALING_POLICY,
                    'targets': ['group'],
                    'properties': {
                        '{0}_instances'.format(instances): {},
                    }
                }
            }
            self.assert_validation(
                ['"{0}_instances" is not a valid integer'.format(instances)],
                groups=groups, nodes=nodes, policies=policies)

    def test_validate_group_and_node_template_same_name(self):
        groups = {
            'node1': ['node2']
        }
        nodes = {
            'node1': None,
            'node2': None,
        }
        self.assert_validation(
            expected_issue_messages=['group has the same name as a node template: node1',
                                     'node template has the same name as a group: node1'],
            groups=groups,
            nodes=nodes)

    def assert_validation(
            self,
            expected_issue_messages,
            groups=None,
            nodes=None,
            policies=None,
            version=None):
        if policies is None:
            policies = {
                'policy': {
                    'type': SCALING_POLICY,
                    'targets': groups.keys(),
                },
            }

        self.template.from_members(
            groups=groups,
            nodes=nodes,
            policies=policies,
            version=version)
        self.assert_parser_issue_messages(
            issue_messages=expected_issue_messages
        )


class TestNodeTemplateDefaultScalableProperties(ParserTestCase):
    def test_default_scalable(self):
        self.assert_scalable_properties()

    def test_default_scalable_empty_capabilities(self):
        self.assert_scalable_properties("""
    capabilities: {}
""")

    def test_default_scalable_empty_scalable(self):
        self.assert_scalable_properties("""
    capabilities:
            scalable: {}
""")

    def test_default_scalable_single_property_defined(self):
        self.assert_scalable_properties("""
    capabilities:
            scalable:
                properties:
                    default_instances: 2
""", expected_default=2)

    def test_instances_deploy_fallback(self):
        """tests backwards compatibility """
        self.assert_scalable_properties("""
    instances:
        deploy: 2
""", expected_default=2)

    def assert_scalable_properties(self, extra='', expected_default=1):
        self.template.version_section('cloudify_dsl', '1.3')
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += extra
        plan = self.parse()
        self.assertEquals({
            'default_instances': expected_default,
            'min_instances': 0,
            'max_instances': UNBOUNDED,
            'current_instances': expected_default,
            'planned_instances': expected_default,
        }, plan['nodes'][0]['capabilities']['scalable']['properties'])

    def test_capabilities_and_instances_deploy_validation(self):
        self.template += """
tosca_definitions_version: test_scaling_policy_and_group_unbounded_literal.0
        """
        self.template.node_type_section()
        self.template.node_template_section()
        self.template += """
    instances:
      deploy: 1
    capabilities: {}
"""
        self.assert_parser_issue_messages(
            ['cannot define "instances" and capabilities together in a '
             'node template'])

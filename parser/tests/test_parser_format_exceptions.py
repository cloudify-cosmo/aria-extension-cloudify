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

from framework.abstract_test_parser import AbstractTestParser


class TestParserFormatExceptions(AbstractTestParser):

    def test_empty_dsl(self):
        self.assert_parser_issue_messages(dsl_string='',
                                          issue_messages=['no content'])

    def test_illegal_yaml_dsl(self):
        yaml = """
plugins:
    plugin1:
        -   item1: {}
    -   bad_format: {}
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["YAML ParserError: expected "
                            "<block end>, but found '-' while parsing a block mapping"])

    def test_no_node_templates(self):
        yaml = """
plugins:
    plugin1:
        executor: central_deployment_agent
        source: dummy
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml, issue_messages=["no node templates"])

    def test_node_templates_list_instead_of_dict(self):
        yaml = """
node_templates:
    - test_node:
        type: test_type
        properties:
            key: "val"
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"node_templates\" in "
                            "\"aria_extension_cloudify.v1_0.templates.ServiceTemplate\" is not a "
                            "dict: [OrderedDict([('test_node', OrderedDict([('type', 'test_type'), "
                            "('properties', OrderedDict([('key', 'val')]))]))])]"])

    def test_name_field_under_node_templates(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    name: my_blueprint
    test_node:
        type: test_type
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"type\" in "
                            "\"aria_extension_cloudify.v1_0.templates.NodeTemplate\" does not have "
                            "a value",
                            "short form not allowed for field \"name\""])

    def test_illegal_first_level_property(self):
        yaml = """
node_types:
    test_type:
        properties:
            key:
                default: 'default'
node_templates:
    test_node:
        type: test_type
        properties:
            key: "val"

illegal_property:
    illegal_sub_property: "some_value"
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"illegal_property\" is not supported in"
                            " \"aria_extension_cloudify.v1_0.templates.ServiceTemplate\""])

    def test_node_with_name(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    test_node:
        name: my_node_name
        type: test_type
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml, issue_messages=["field \"name\" is not supported in \"test_node\""])

    def test_node_properties_as_list(self):
        yaml = """
node_templates:
    test_node:
        -   type: test_type
            properties:
                key: "val"
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"type\" in "
                            "\"aria_extension_cloudify.v1_0.templates.NodeTemplate\" does not "
                            "have a value",
                            "short form not allowed for field \"test_node\""])

    def test_node_without_type_declaration(self):
        yaml = """
node_templates:
    test_node:
        properties:
            key: "val"
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"type\" in "
                            "\"aria_extension_cloudify.v1_0.templates.NodeTemplate\" "
                            "does not have a value"])

    def test_type_with_illegal_interface_declaration(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                - should: be a dict
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"test_interface1\"",
                            "assignment to undefined property \"key\" in \"test_node\""])

    def test_type_with_illegal_interface_declaration_2(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                1 # not a string
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"test_interface1\"",
                            "assignment to undefined property \"key\" in \"test_node\""])

    def test_type_with_illegal_interface_declaration_3(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                a: 1 # key not a string
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=[
                "field \"implementation\" in \"aria_extension_cloudify.v1_0.definitions.OperationDefinition\" is not a valid \"str\": 1",
                "assignment to undefined property \"key\" in \"test_node\""])

    def test_node_extra_properties(self):
        # testing for additional properties directly under node
        # (i.e. not within the node's 'properties' section)
        yaml = self.MINIMAL_BLUEPRINT + """
        extra_property: "val"
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"test_node\""])

    def test_import_bad_syntax(self):
        yaml = """
imports: fake-file.yaml
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"imports\" in "
                            "\"aria_extension_cloudify.v1_0.templates.ServiceTemplate\" "
                            "is not a list: 'fake-file.yaml'"])

    def test_import_bad_syntax2(self):
        yaml = """
imports:
    first_file: fake-file.yaml
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"imports\" in "
                            "\"aria_extension_cloudify.v1_0.templates.ServiceTemplate\" "
                            "is not a list: OrderedDict([('first_file', 'fake-file.yaml')])"])

    def test_import_bad_syntax3(self):
        yaml = """
imports:
    -   first_file: fake-file.yaml
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["location: OrderedDict([('first_file', 'fake-file.yaml')])"])

    def test_duplicate_import_in_same_file(self):
        yaml = """
imports:
    -   fake-file.yaml
    -   fake-file2.yaml
    -   fake-file.yaml
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=[
                "field \"imports\" in \"aria_extension_cloudify.v1_0.templates.ServiceTemplate\" has a duplicate \"str\": 'fake-file.yaml'"])

    def test_type_multiple_derivation(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: "not_val"
        derived_from:
            -   "test_type_parent"
            -   "test_type_parent2"

    test_type_parent:
        properties:
            key:
                default: "val1_parent"
    test_type_parent2:
        properties:
            key:
                default: "val1_parent2"
    """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"derived_from\" in \"aria_extension_cloudify.v1_0.types.NodeType\" is not a valid \"str\": ['test_type_parent', 'test_type_parent2']"])

    def test_plugin_without_executor_field(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        source: dummy
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"executor\" in "
                            "\"aria_extension_cloudify.v1_0.misc.Plugin\" does not have a value"])

    def test_plugin_extra_properties(self):
        yaml = self.MINIMAL_BLUEPRINT + """
plugins:
    test_plugin:
        executor: central_deployment_agent
        source: dummy
        another_field: bad
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"another_field\" is not supported in \"test_plugin\""])

    def test_top_level_relationships_bad_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    extra_prop: "val"
                """
        self.assert_parser_issue_messages(
            dsl_string=yaml, issue_messages=["short form not allowed for field \"extra_prop\""])

    def test_top_level_relationships_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        extra_prop: "val"
                """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_prop\" is not supported in \"test_relationship\""])

    def test_top_level_relationships_interface_with_operations_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        source_interfaces:
            test_rel_interface: string
                """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"test_rel_interface\""])

    def test_type_relationship(self):
        # relationships are not valid under types whatsoever.
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        relationships: {}
        """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"relationships\" is not supported in \"test_type\""])

    def test_instance_relationships_relationship_without_type(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   target: test_node2
    test_node2:
        type: test_type
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"type\" in "
                            "\"aria_extension_cloudify.v1_0.templates.RelationshipTemplate\" "
                            "does not have a value"])

    def test_instance_relationships_relationship_without_target(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
relationships:
    relationship: {}
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"target\" in "
                            "\"aria_extension_cloudify.v1_0.templates.RelationshipTemplate\" "
                            "does not have a value"])

    def test_instance_relationships_relationship_extra_prop(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
                target: "test_node2"
                extra_prop: "value"
    test_node2:
        type: test_type
relationships:
    relationship: {}
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_prop\" is not supported in \"test_node\""])

    def test_instance_relationships_relationship_with_derived_from_field(self):
        # derived_from field is not valid under an instance relationship
        # definition
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            -   type: relationship
                target: test_node2
                derived_from: "relationship"
    test_node2:
        type: test_type
relationships:
    relationship: {}
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"derived_from\" is not supported in \"test_node\""])

    def test_instance_relationships_relationship_object(self):
        # trying to use a dictionary instead of an array
        yaml = self.MINIMAL_BLUEPRINT + """
        relationships:
            test_relationship:
                type: "fake_relationship"
                target: "fake_node"
                derived_from: "relationship"
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"relationships\" in "
                            "\"aria_extension_cloudify.v1_0.templates.NodeTemplate\" "
                            "is not a list: OrderedDict([('test_relationship', "
                            "OrderedDict([('type', 'fake_relationship'), "
                            "('target', 'fake_node'), ('derived_from', 'relationship')]))])"])

    def test_multiple_instances_with_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: 2
            extra_prop: value
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_prop\" is not supported in \"test_node\""])

    def test_multiple_instances_without_deploy_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances: {}
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["f"])

    def test_multiple_instances_string_value(self):
        yaml = self.MINIMAL_BLUEPRINT + """
        instances:
            deploy: '2'
            """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"deploy\" in \"aria_extension_cloudify.v1_0.misc.Instances\" is not a valid \"int\": '2'"])

    def test_interface_operation_mapping_no_mapping_prop(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                  properties:
                      key: "value"
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" is not supported in \"install\""])

    def test_workflow_mapping_invalid_value(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1: 123
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"mapping\" in \"aria_extension_cloudify.v1_0.definitions.WorkflowDefinition\" is not a valid \"str\": 123"])

    def test_workflow_mapping_no_mapping_field(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        parameters:
            param: {}
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"mapping\" in "
                            "\"aria_extension_cloudify.v1_0.definitions.WorkflowDefinition\" "
                            "does not have a value"])

    def test_workflow_parameters_simple_dictionary_schema_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_workflow_parameters_array_dictionary_schema_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key:
                - default: val1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_workflow_parameters_schema_array_format(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            - key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"parameters\" in"
                            " \"aria_extension_cloudify.v1_0.definitions.WorkflowDefinition\" "
                            "is not a dict: [OrderedDict([('key', 'value')])]"])

    def test_workflow_parameters_extra_property(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        parameters:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"key\""])

    def test_workflow_properties_instead_of_parameters(self):
        yaml = self.BLUEPRINT_WITH_INTERFACES_AND_PLUGINS + """
workflows:
    workflow1:
        mapping: test_plugin.workflow1
        properties:
            key:
                default: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" is not supported in \"workflow1\""])

    def test_interface_operation_mapping_unknown_extra_attributes(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + self.BASIC_PLUGIN + """
node_types:
    test_type:
        interfaces:
            test_interface1:
                install:
                  implementation: test_plugin.install
                  inputs:
                      key: 'value'
                  unknown: 'bla'
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"unknown\" is not supported in \"install\"",
                            "short form not allowed for field \"key\""])

    def test_type_properties_simple_dictionary_schema_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_type_properties_array_dictionary_schema_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                - default: val1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_type_properties_schema_array_format(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            - key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" in "
                            "\"aria_extension_cloudify.v1_0.types.NodeType\" "
                            "is not a dict: [OrderedDict([('key', 'value')])]"])

    def test_type_properties_extra_property(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"key\""])

    def test_relationship_properties_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_relationship_properties_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                - default: val1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_relationship_properties_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            - key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" in "
                            "\"aria_extension_cloudify.v1_0.types.RelationshipType\" "
                            "is not a dict: [OrderedDict([('key', 'value')])]"])

    def test_relationship_properties_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
relationships:
    test_relationship:
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"key\""])

    def test_policy_type_properties_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_policy_type_properties_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key:
                - default: val1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_policy_type_properties_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            - key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" in "
                            "\"aria_extension_cloudify.v1_0.types.PolicyType\" "
                            "is not a dict: [OrderedDict([('key', 'value')])]"])

    def test_policy_type_properties_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: source
        properties:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"key\""])

    def test_policy_type_source_non_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        source: 1
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"source\" in \"aria_extension_cloudify.v1_0.types.PolicyType\" is not a valid \"str\": 1"])

    def test_policy_type_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        extra_property: i_should_not_be_here
        source: source
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"test_policy\""])

    def test_policy_type_missing_source(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    test_policy:
        properties:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"source\" in "
                            "\"aria_extension_cloudify.v1_0.types.PolicyType\" "
                            "does not have a value"])

    def test_policy_triggers_parameters_simple_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_policy_triggers_parameters_array_dictionary_schema_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key:
                - default: val1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["short form not allowed for field \"key\""])

    def test_policy_triggers_parameters_schema_array_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            - key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"parameters\" in "
                            "\"aria_extension_cloudify.v1_0.types.GroupPolicyTriggerType\" "
                            "is not a dict: [OrderedDict([('key', 'value')])]"])

    def test_policy_triggers_parameters_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: source
        parameters:
            key:
                default: val1
                description: property_desc1
                extra_property: this_is_not_allowed
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"key\""])

    def test_policy_trigger_source_non_string(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        source: 1
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"source\" in \"aria_extension_cloudify.v1_0.types.GroupPolicyTriggerType\" is not a valid \"str\": 1"])

    def test_policy_trigger_extra_property(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        extra_property: i_should_not_be_here
        source: source
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"test_trigger\""])

    def test_policy_trigger_missing_source(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_triggers:
    test_trigger:
        parameters:
            key:
                default: val1
                description: property_desc1
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"source\" in "
                            "\"aria_extension_cloudify.v1_0.types.GroupPolicyTriggerType\" "
                            "does not have a value"])

    def test_groups_missing_member(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        policies:
            policy:
                type: type
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"members\" in"
                            " \"aria_extension_cloudify.v1_0.templates.GroupTemplate\" "
                            "does not have a value"])

    def test_groups_extra_property(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                type: type
        extra_property: extra_property
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"group\""])

    def test_groups_policy_missing_type(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                properties:
                    key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["required field \"type\" in "
                            "\"aria_extension_cloudify.v1_0.assignments.GroupPolicyAssignment\" "
                            "does not have a value"])

    def test_groups_policy_extra_property(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    member:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [member]
        policies:
            policy:
                type: type
                extra_property: extra_property
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"extra_property\" is not supported in \"policy\""])

    def test_group_members_bad_type1(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [1]
        policies:
            policy:
                type: type
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["\"members\" refers to an unknown node template "
                            "or group in \"group\": [u'1']"])

    def test_group_members_bad_type2(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: 1
        policies:
            policy:
                type: type
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"members\" in "
                            "\"aria_extension_cloudify.v1_0.templates.GroupTemplate\" "
                            "is not a list: 1"])

    def test_group_policy_type_bad_type(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    vm:
        type: test_type
groups:
    group:
        members: [vm]
        policies:
            policy:
                type: 1
                properties:
                    key: value
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["\"type\" refers to an unknown policy type in \"policy\": u'1'",
                            "assignment to undefined property \"key\" in \"policy\""])

    def test_group_policy_type_bad_properties(self):
        yaml = """
node_types:
    test_type: {}
node_templates:
    vm:
        type: test_type
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: [vm]
        policies:
            policy:
                type: type
                properties: properties
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["field \"properties\" in "
                            "\"aria_extension_cloudify.v1_0.assignments.GroupPolicyAssignment\" "
                            "is not a dict: \'properties\'"])

    def test_group_no_members(self):
        yaml = self.MINIMAL_BLUEPRINT + """
policy_types:
    type:
        properties: {}
        source: source
groups:
    group:
        members: []
        policies:
            policy:
                type: type
                properties: {}
"""
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["group \"group\" has no members"])

    def test_unknown_property_schema_type(self):
        yaml = self.BASIC_NODE_TEMPLATES_SECTION + """
node_types:
    test_type:
        properties:
            key:
                type: unknown-type
                """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["\"type\" refers to an unknown data type "
                            "in \"key\": u\'unknown-type\'"])

    def test_invalid_version_field_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
tosca_definitions_version: [cloudify_dsl_1_0]
    """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["s"])

    def test_invalid_blueprint_description_field_format(self):
        yaml = self.MINIMAL_BLUEPRINT + """
description:
  nested_key: value
  """
        self.assert_parser_issue_messages(
            dsl_string=yaml,
            issue_messages=["\"description\" is not a valid \"str\": {'nested_key': 'value'}"])

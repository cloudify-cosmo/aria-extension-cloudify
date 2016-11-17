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

from .assignments import CapabilityAssignment
from .field_validators import node_templates_or_groups_validator, policy_type_validator
from .modeling.node_templates import get_node_template_scalable
from ..v1_0 import GroupTemplate as GroupTemplate1_0, PropertyAssignment
from ..v1_1 import NodeTemplate as NodeTemplate1_1
from ..v1_2 import ServiceTemplate as ServiceTemplate1_2
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, primitive_list_field, object_dict_field, field_validator, list_type_validator
from aria.validation import Issue
from aria.utils import FrozenList, cachedmethod

@has_fields
@dsl_specification('node-templates-1', 'cloudify-1.3')
class NodeTemplate(NodeTemplate1_1):
    @object_dict_field(CapabilityAssignment)
    def capabilities(self):
        """
        Used for specifying the node template capabilities (Supported since: :code:`cloudify_dsl_1_3`. At the moment only scalable capability is supported)
        
        :rtype: dict of str, :class:`CapabilityAssignment`
        """

    @cachedmethod
    def _get_scalable(self, context):
        return get_node_template_scalable(context, self)

    def _validate(self, context):
        super(NodeTemplate, self)._validate(context)
        groups = context.presentation.get('service_template', 'groups')
        if (groups is not None) and (self._name in groups):
            context.validation.report('node template has the same name as a group: %s' % self._name, locator=self._locator, level=Issue.BETWEEN_TYPES)

@has_fields
@dsl_specification('groups', 'cloudify-1.3')
class GroupTemplate(GroupTemplate1_0):
    """
    Groups provide a way of configuring shared behavior for different sets of :code:`node_templates`.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-groups/>`__.
    """

    @field_validator(node_templates_or_groups_validator)
    @primitive_list_field(str, required=True)
    def members(self):
        """
        A list of group members. Members are node template names or other group names. 
        
        :rtype: list of str
        """

    def _validate(self, context):
        super(GroupTemplate, self)._validate(context)
        node_templates = context.presentation.get('service_template', 'node_templates')
        if (node_templates is not None) and (self._name in node_templates):
            context.validation.report('group has the same name as a node template: %s' % self._name, locator=self._locator, level=Issue.BETWEEN_TYPES)

@has_fields
@dsl_specification('policies', 'cloudify-1.3')
class PolicyTemplate(Presentation):
    """
    Policies provide a way of configuring reusable behavior by referencing groups for which a policy applies.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-policies/>`__.    
    """
    
    @field_validator(policy_type_validator)
    @primitive_field(str, required=True)
    def type(self):
        """
        The policy type.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        The specific policy properties. The properties schema is defined by the policy type.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """

    @field_validator(list_type_validator('group', 'groups'))
    @primitive_list_field(str, required=True)
    def targets(self):
        """
        A list of group names. The policy will be applied on the groups specified in this list. 
        
        :rtype: list of str
        """
    
    @cachedmethod
    def _get_type(self, context):
        return context.presentation.get_from_dict('service_template', 'policy_types', self.type)

    @cachedmethod
    def _get_targets(self, context):
        r = []
        targets = self.targets
        if targets:
            for target in targets:
                target = context.presentation.get_from_dict('service_template', 'groups', target)
                if target is not None:
                    r.append(target)
        return FrozenList(r)

    def _validate(self, context):
        super(PolicyTemplate, self)._validate(context)
        self._get_targets(context)

@has_fields
class ServiceTemplate(ServiceTemplate1_2):
    @object_dict_field(NodeTemplate)
    def node_templates(self):
        """
        :rtype: dict of str, :class:`NodeTemplate`
        """

    @object_dict_field(GroupTemplate)
    def groups(self):
        """
        :rtype: dict of str, :class:`GroupTemplate`
        """

    @object_dict_field(PolicyTemplate)
    def policies(self):
        """
        :rtype: dict of str, :class:`PolicyTemplate`
        """

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'tosca_definitions_version',
            'imports',
            'plugins',
            'data_types',
            'node_types',
            'policy_types',
            'inputs',
            'node_templates',
            'relationships',
            'groups',
            'policies',
            'policy_triggers',
            'outputs',
            'workflows',
            'upload_resources'))

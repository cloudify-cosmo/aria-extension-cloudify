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

from .definitions import PropertyDefinition, WorkflowDefinition
from .assignments import PropertyAssignment, InterfaceAssignment, GroupPolicyAssignment
from .types import NodeType, RelationshipType, PolicyType, GroupPolicyTriggerType
from .misc import Description, Output, Plugin, Instances
from .modeling.properties import get_assigned_and_defined_property_values, get_parameter_values
from .modeling.interfaces import get_template_interfaces
from .modeling.relationships import get_relationship_assigned_and_defined_property_values
from .modeling.node_templates import get_node_template_scalable
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, primitive_list_field, object_field, object_list_field, object_dict_field, field_validator, type_validator, list_type_validator
from aria.utils import FrozenDict, cachedmethod

@has_fields
@dsl_specification('relationships-1', 'cloudify-1.0')
class RelationshipTemplate(Presentation):
    """
    :code:`relationships` let you define how nodes relate to one another. For example, a :code:`web_server` node can be :code:`contained_in` a :code:`vm` node or an :code:`application` node can be :code:`connected_to` a :code:`database` node.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-relationships/>`__
    """

    @object_field(Description)
    def description(self):
        """
        ARIA NOTE: Not mentioned in the spec.
        
        :rtype: :class:`Description`
        """

    @field_validator(type_validator('relationship', 'relationships'))
    @primitive_field(str, required=True)
    def type(self):
        """
        Either a newly declared relationship type or one of the relationship types provided by default when importing the types.yaml file.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        ARIA NOTE: This field is not mentioned in the spec, but is implied.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """
    
    @field_validator(type_validator('node template', 'node_templates'))
    @primitive_field(str, required=True)
    def target(self):
        """
        The node's name to relate the current node to.
        
        :rtype: str
        """

    @object_dict_field(InterfaceAssignment)
    def source_interfaces(self):
        """
        A dict of interfaces.
        
        :rtype: dict of str, :class:`InterfaceAssignment`
        """

    @object_dict_field(InterfaceAssignment)
    def target_interfaces(self):
        """
        A dict of interfaces.
        
        :rtype: dict of str, :class:`InterfaceAssignment`
        """

    @cachedmethod
    def _get_type(self, context):
        return context.presentation.get_from_dict('service_template', 'relationships', self.type)

    @cachedmethod
    def _get_property_values(self, context):
        return FrozenDict(get_relationship_assigned_and_defined_property_values(context, self))

    @cachedmethod
    def _get_source_interfaces(self, context):
        return FrozenDict(get_template_interfaces(context, self, 'relationship template', 'source_interfaces', '_get_source_interfaces'))

    @cachedmethod
    def _get_target_interfaces(self, context):
        return FrozenDict(get_template_interfaces(context, self, 'relationship template', 'target_interfaces', '_get_target_interfaces'))

    def _validate(self, context):
        super(RelationshipTemplate, self)._validate(context)
        self._get_property_values(context)
        self._get_source_interfaces(context)
        self._get_target_interfaces(context)

@has_fields
@dsl_specification('node-templates', 'cloudify-1.0')
class NodeTemplate(Presentation):
    """
    :code:`node_templates` represent the actual instances of node types which would eventually represent a running application/service as described in the blueprint.

    :code:`node_templates` are more commonly referred to as :code:`nodes`. Nodes can comprise more than one instance. For example, you could define a node which contains two vms. Each vm will then be called a :code:`node_instance`.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-node-templates/>`__
    """

    @object_field(Description)
    def description(self):
        """
        ARIA NOTE: Not mentioned in the spec.
        
        :rtype: :class:`Description`
        """

    @field_validator(type_validator('node type', 'node_types'))
    @primitive_field(str, required=True)
    def type(self):
        """
        The node-type of this node template.
        
        :rtype: str
        """

    @object_dict_field(PropertyAssignment)
    def properties(self):
        """
        The properties of the node template matching its node type properties schema.
        
        :rtype: dict of str, :class:`PropertyAssignment`
        """
    
    @object_dict_field(InterfaceAssignment)
    def interfaces(self):
        """
        Used for mapping plugins to interfaces operation or for specifying inputs for already mapped node type operations.
        
        :rtype: dict of str, :class:`InterfaceAssignment`
        """
    
    @object_list_field(RelationshipTemplate)
    def relationships(self):
        """
        Used for specifying the relationships this node template has with other node templates.
        
        :rtype: list of :class:`RelationshipTemplate`
        """

    @object_field(Instances)
    def instances(self):
        """
        Instances configuration. (Deprecated. Replaced by :code:`capabilities.scalable`.)
        
        :rtype: :class:`Instances`
        """
    
    @cachedmethod
    def _get_type(self, context):
        return context.presentation.get_from_dict('service_template', 'node_types', self.type)

    @cachedmethod
    def _get_property_values(self, context):
        return FrozenDict(get_assigned_and_defined_property_values(context, self))

    @cachedmethod
    def _get_interfaces(self, context):
        return FrozenDict(get_template_interfaces(context, self, 'node template', 'interfaces', '_get_interfaces'))

    @cachedmethod
    def _get_scalable(self, context):
        return get_node_template_scalable(context, self)

    def _validate(self, context):
        super(NodeTemplate, self)._validate(context)
        self._get_property_values(context)
        self._get_interfaces(context)
        self._get_scalable(context)

@has_fields
@dsl_specification('groups', 'cloudify-1.0')
@dsl_specification('groups', 'cloudify-1.1')
@dsl_specification('groups', 'cloudify-1.2')
class GroupTemplate(Presentation):
    """
    Groups provide a way of configuring shared behavior for different sets of :code:`node_templates`.
    
    See the `Cloudify DSL v1.2 specification <http://docs.getcloudify.org/3.3.1/blueprints/spec-groups/>`__.
    """

    @field_validator(list_type_validator('node template', 'node_templates'))
    @primitive_list_field(str, required=True)
    def members(self):
        """
        A list of group members. Members are node template names. 
        
        :rtype: list of str
        """

    @object_dict_field(GroupPolicyAssignment)
    def policies(self):
        """
        A dict of policies. 
        
        :rtype: dict of str, :class:`GroupPolicyAssignment`
        """

@has_fields
class ServiceTemplate(Presentation):
    @primitive_field(str)
    @dsl_specification('versioning', 'cloudify-1.0')
    @dsl_specification('versioning', 'cloudify-1.1')
    @dsl_specification('versioning', 'cloudify-1.2')
    @dsl_specification('versioning', 'cloudify-1.3')
    def tosca_definitions_version(self):
        """
        :code:`tosca_definitions_version` is a top level property of the blueprint which is used to specify the DSL version used. For Cloudify 3.4, the versions that are currently defined are :code:`cloudify_dsl_1_0`, :code:`cloudify_dsl_1_1`, :code:`cloudify_dsl_1_2` and :code:`cloudify_dsl_1_3`.

        The version declaration must be included in the main blueprint file. It may also be included in YAML files that are imported in it (transitively), in which case, the version specified in the imported YAMLs must match the version specified in the main blueprint file.

        In future Cloudify versions, as the DSL specification evolves, this mechanism will enable providing backward compatibility for blueprints written in older versions. 
        
        See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-versioning/>`__
        
        :rtype: str
        """

    @primitive_list_field(str)
    @dsl_specification('imports', 'cloudify-1.0')
    @dsl_specification('imports', 'cloudify-1.1')
    @dsl_specification('imports', 'cloudify-1.2')
    @dsl_specification('imports', 'cloudify-1.3')
    def imports(self):
        """
        :code:`imports` allow the author of a blueprint to reuse blueprint files or parts of them and use predefined types (e.g. from the types.yaml file).
        
        See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-imports/>`__
        
        :rtype: list of :class:`Import`
        """

    @object_dict_field(PropertyDefinition)
    @dsl_specification('inputs', 'cloudify-1.0')
    @dsl_specification('inputs', 'cloudify-1.1')
    def inputs(self):
        """
        :code:`inputs` are parameters injected into the blueprint upon deployment creation. These parameters can be referenced by using the :code:`get_input` intrinsic function.

        Inputs are useful when there's a need to inject parameters to the blueprint which were unknown when the blueprint was created and can be used for distinction between different deployments of the same blueprint.
        
        See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-inputs/>`__
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @object_dict_field(NodeTemplate)
    def node_templates(self):
        """
        :rtype: dict of str, :class:`NodeTemplate`
        """

    @object_dict_field(NodeType)
    def node_types(self):
        """
        :rtype: dict of str, :class:`NodeType`
        """

    @object_dict_field(Output)
    def outputs(self):
        """
        :rtype: dict of str, :class:`Output`
        """

    @object_dict_field(RelationshipType)
    def relationships(self):
        """
        :rtype: dict of str, :class:`RelationshipType`
        """

    @object_dict_field(Plugin)
    def plugins(self):
        """
        :rtype: dict of str, :class:`Plugin`
        """
    
    @object_dict_field(WorkflowDefinition)
    def workflows(self):
        """
        :rtype: dict of str, :class:`WorkflowDefinition`
        """

    @object_dict_field(GroupTemplate)
    def groups(self):
        """
        :rtype: dict of str, :class:`GroupTemplate`
        """

    @object_dict_field(PolicyType)
    def policy_types(self):
        """
        :rtype: dict of str, :class:`GroupPolicyType`
        """

    @object_dict_field(GroupPolicyTriggerType)
    def policy_triggers(self):
        """
        :rtype: dict of str, :class:`GroupPolicyTriggerType`
        """

    @cachedmethod
    def _get_input_values(self, context):
        return FrozenDict(get_parameter_values(context, self, 'inputs'))

    @cachedmethod
    def _get_output_values(self, context):
        return FrozenDict(get_parameter_values(context, self, 'outputs'))

    def _validate(self, context):
        super(ServiceTemplate, self)._validate(context)
        self._get_input_values(context)
        self._get_output_values(context)

    def _dump(self, context):
        self._dump_content(context, (
            'description',
            'tosca_definitions_version',
            'imports',
            'plugins',
            'node_types',
            'policy_types',
            'inputs',
            'node_templates',
            'relationships',
            'groups',
            'policy_triggers',
            'outputs',
            'workflows'))

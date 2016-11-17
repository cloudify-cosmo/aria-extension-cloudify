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

from .definitions import InterfaceDefinition, PropertyDefinition
from .modeling.properties import get_inherited_property_definitions
from .modeling.interfaces import get_inherited_interface_definitions
from .modeling.relationships import get_relationship_inherited_property_definitions
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, object_dict_field, field_validator, derived_from_validator, get_parent_presentation
from aria.utils import FrozenDict, cachedmethod

@has_fields
@dsl_specification('node-types', 'cloudify-1.0')
class NodeType(Presentation):
    """
    :code:`node_types` are used for defining common properties and behaviors for :code:`node_templates`. :code:`node_templates` can then be created based on these types, inheriting their definitions.

    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-node-types/>`__
    """

    @primitive_field(str)
    def description(self):
        """
        ARIA NOTE: Not mentioned in the spec.
        
        :rtype: str
        """

    @field_validator(derived_from_validator('node_types'))
    @primitive_field(str)
    def derived_from(self):
        """
        A string referencing a parent type.
        
        :rtype: str
        """

    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        A dictionary of node interfaces.
        
        :rtype: dict of str, :class:`InterfaceDefinition`
        """
    
    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        A dictionary of node interfaces.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, 'node_types')

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_inherited_property_definitions(context, self, 'properties'))

    @cachedmethod
    def _get_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'node type', 'interfaces'))

    def _validate(self, context):
        super(NodeType, self)._validate(context)
        self._get_properties(context)
        self._get_interfaces(context)

@has_fields
@dsl_specification('relationships-2', 'cloudify-1.0')
class RelationshipType(Presentation):
    """
    You can declare your own relationship types in the relationships section in the blueprint. This is useful when you want to change the default implementation of how nodes interact.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-relationships/#declaring-relationship-types>`__
    """

    @primitive_field(str)
    def description(self):
        """
        ARIA NOTE: Not mentioned in the spec.
        
        :rtype: str
        """

    @field_validator(derived_from_validator('relationships'))
    @primitive_field(str)
    def derived_from(self):
        """
        The relationship type from which the new relationship is derived.
        
        :rtype: str
        """

    @object_dict_field(InterfaceDefinition)
    def source_interfaces(self):
        """
        A dict of interfaces.
        
        :rtype: dict of str, :class:`InterfaceDefinition`
        """

    @object_dict_field(InterfaceDefinition)
    def target_interfaces(self):
        """
        A dict of interfaces.
        
        :rtype: dict of str, :class:`InterfaceDefinition`
        """
    
    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        ARIA NOTE: This field is not mentioned in the spec, but is implied.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return get_parent_presentation(context, self, 'relationships')

    @cachedmethod
    def _get_properties(self, context):
        return FrozenDict(get_relationship_inherited_property_definitions(context, self))

    @cachedmethod
    def _get_source_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'relationship type', 'source_interfaces'))

    @cachedmethod
    def _get_target_interfaces(self, context):
        return FrozenDict(get_inherited_interface_definitions(context, self, 'relationship type', 'target_interfaces'))

    def _validate(self, context):
        super(RelationshipType, self)._validate(context)
        self._get_properties(context)
        self._get_source_interfaces(context)
        self._get_target_interfaces(context)

@has_fields
@dsl_specification('policy-types', 'cloudify-1.0')
@dsl_specification('policy-types', 'cloudify-1.1')
class PolicyType(Presentation):
    """
    :code:`policies` provide a way of analyzing a stream of events that correspond to a group of nodes (and their instances).
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-policy-types/>`__.
    """

    @primitive_field(str)
    def description(self):
        """
        ARIA NOTE: Not mentioned in the spec.
        
        :rtype: str
        """

    @primitive_field(str, required=True)
    def source(self):
        """
        The policy trigger implementation source (URL or a path relative to the blueprint root directory).
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def properties(self):
        """
        Optional properties schema for the policy type.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return None

    @cachedmethod
    def _get_properties(self, context):
        return self.properties

@has_fields
@dsl_specification('policy-triggers', 'cloudify-1.0')
@dsl_specification('policy-triggers', 'cloudify-1.1')
class GroupPolicyTriggerType(Presentation):
    """
    :code:`policy_triggers` specify the implementation of actions invoked by policies and declare the properties that define the trigger's behavior.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-policy-triggers/>`__.
    """

    @primitive_field(str, required=True)
    def source(self):
        """
        The policy trigger implementation source (URL or a path relative to the blueprint root directory).
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def parameters(self):
        """
        Optional parameters schema for the policy trigger.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @cachedmethod
    def _get_parent(self, context):
        return None

    @cachedmethod
    def _get_properties(self, context):
        return self.parameters

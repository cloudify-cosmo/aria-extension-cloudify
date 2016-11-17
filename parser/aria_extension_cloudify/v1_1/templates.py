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

from .assignments import InterfaceAssignment
from .misc import Plugin
from ..v1_0 import ServiceTemplate as ServiceTemplate1_0, RelationshipTemplate as RelationshipTemplate1_0, NodeTemplate as NodeTemplate1_0
from aria import dsl_specification
from aria.presentation import has_fields, object_dict_field, object_list_field

@has_fields
@dsl_specification('relationships-1', 'cloudify-1.1')
@dsl_specification('relationships-1', 'cloudify-1.2')
@dsl_specification('relationships-1', 'cloudify-1.3')
class RelationshipTemplate(RelationshipTemplate1_0):
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

@has_fields
@dsl_specification('node-templates', 'cloudify-1.1')
@dsl_specification('node-templates', 'cloudify-1.2')
class NodeTemplate(NodeTemplate1_0):
    @object_list_field(RelationshipTemplate)
    def relationships(self):
        """
        Used for specifying the relationships this node template has with other node templates.
        
        :rtype: list of :class:`RelationshipTemplate`
        """

    @object_dict_field(InterfaceAssignment)
    def interfaces(self):
        """
        Used for mapping plugins to interfaces operation or for specifying inputs for already mapped node type operations.
        
        :rtype: dict of str, :class:`InterfaceAssignment`
        """

@has_fields
class ServiceTemplate(ServiceTemplate1_0):
    @object_dict_field(NodeTemplate)
    def node_templates(self):
        """
        :rtype: dict of str, :class:`NodeTemplate`
        """

    @object_dict_field(Plugin)
    def plugins(self):
        """
        :rtype: dict of str, :class:`Plugin`
        """

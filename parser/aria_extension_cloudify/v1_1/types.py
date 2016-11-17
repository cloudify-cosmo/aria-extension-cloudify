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

from ..v1_0 import NodeType as NodeType1_0, RelationshipType as RelationshipType1_0
from .definitions import InterfaceDefinition
from aria import dsl_specification
from aria.presentation import has_fields, object_dict_field

@has_fields
@dsl_specification('node-types', 'cloudify-1.1')
class NodeType(NodeType1_0):
    @object_dict_field(InterfaceDefinition)
    def interfaces(self):
        """
        A dictionary of node interfaces.
        
        :rtype: dict of str, :class:`InterfaceDefinition`
        """

@has_fields
@dsl_specification('relationships-2', 'cloudify-1.1')
class RelationshipType(RelationshipType1_0):
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

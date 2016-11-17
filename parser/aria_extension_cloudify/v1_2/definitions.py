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

from ..v1_0 import PropertyDefinition as PropertyDefinition1_0, WorkflowDefinition as WorkflowDefinition1_0
from ..v1_1 import OperationDefinition as OperationDefinition1_1, InterfaceDefinition as InterfaceDefinition1_1
from aria import dsl_specification
from aria.presentation import has_fields, allow_unknown_fields, short_form_field, primitive_field, object_dict_field, object_dict_unknown_fields

@has_fields
class PropertyDefinition(PropertyDefinition1_0):
    @primitive_field(bool, default=True)
    def required(self):
        """
        Specifies whether the property is required. (Default: true, Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: bool
        """

@short_form_field('implementation')
@has_fields
class OperationDefinition(OperationDefinition1_1):
    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        Schema of inputs that will be passed to the implementation as kwargs.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-1', 'cloudify-1.2')
@dsl_specification('interfaces-1', 'cloudify-1.3')
class InterfaceDefinition(InterfaceDefinition1_1):
    @object_dict_unknown_fields(OperationDefinition)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationDefinition`
        """

@short_form_field('mapping')
@has_fields
@dsl_specification('workflows', 'cloudify-1.2')
@dsl_specification('workflows', 'cloudify-1.3')
class WorkflowDefinition(WorkflowDefinition1_0):
    @object_dict_field(PropertyDefinition)
    def parameters(self):
        """
        A map of parameters to be passed to the workflow implementation
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

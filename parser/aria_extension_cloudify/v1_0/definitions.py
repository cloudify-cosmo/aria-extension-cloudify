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

from .misc import Description
from .presentation.field_validators import data_type_validator, data_value_validator
from .modeling.data_types import get_data_type
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, allow_unknown_fields, short_form_field, primitive_field, object_field, object_dict_field, object_dict_unknown_fields, field_validator
from aria.utils import cachedmethod

@has_fields
class PropertyDefinition(Presentation):
    @object_field(Description)
    def description(self):
        """
        Description for the property.
        
        :rtype: :class:`Description`
        """

    @field_validator(data_type_validator)
    @primitive_field(str)
    def type(self):
        """
        Property type. Not specifying a data type means the type can be anything (including types not listed in the valid types). Valid types: string, integer, float, boolean or a custom data type.
        
        :rtype: str
        """

    @field_validator(data_value_validator)
    @primitive_field()
    def default(self):
        """
        An optional default value for the property.        
        """

    @cachedmethod
    def _get_type(self, context):
        return get_data_type(context, self)

@short_form_field('implementation')
@has_fields
class OperationDefinition(Presentation):
    @primitive_field(str)
    def implementation(self):
        """
        The script or plugin task name to execute.
        
        ARIA NOTE: The spec seems to mistakingly mark this as a required field.
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def inputs(self):
        """
        Schema of inputs that will be passed to the implementation as kwargs.
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

    @primitive_field(str, allowed=('central_deployment_agent', 'host_agent'))
    def executor(self):
        """
        Valid values: :code:`central_deployment_agent`, :code:`host_agent`.
        
        :rtype: str
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-1', 'cloudify-1.0')
class InterfaceDefinition(Presentation):
    """
    Interfaces provide a way to map logical tasks to executable operations.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-interfaces/>`__.
    """

    @object_dict_unknown_fields(OperationDefinition)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationDefinition`
        """

@short_form_field('mapping')
@has_fields
@dsl_specification('workflows', 'cloudify-1.0')
@dsl_specification('workflows', 'cloudify-1.1')
class WorkflowDefinition(Presentation):
    """
    :code:`workflows` define a set of tasks that can be executed on a node or a group of nodes, and the execution order of these tasks, serially or in parallel. A task may be an operation (implemented by a plugin), but it may also be other actions, including arbitrary code.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-workflows/>`__.
    """

    @primitive_field(str, required=True)
    def mapping(self):
        """
        A path to the method implementing this workflow (In the "Simple mapping" format this value is set without explicitly using the "mapping" key)
        
        :rtype: str
        """

    @object_dict_field(PropertyDefinition)
    def parameters(self):
        """
        A map of parameters to be passed to the workflow implementation
        
        :rtype: dict of str, :class:`PropertyDefinition`
        """

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

from ..v1_0 import OperationAssignment as OperationAssignment1_0, InterfaceAssignment as InterfaceAssignment1_0
from aria import dsl_specification
from aria.presentation import has_fields, allow_unknown_fields, short_form_field, primitive_field, object_dict_unknown_fields

@short_form_field('implementation')
@has_fields
class OperationAssignment(OperationAssignment1_0):
    @primitive_field(int)
    def max_retries(self):
        """
        Maximum number of retries for a task. -1 means infinite retries (Default: :code:`task_retries` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retries` workflow configuration for local workflows).
        
        :rtype: int
        """

    @primitive_field(int)
    def retry_interval(self):
        """
        Minimum wait time (in seconds) in between task retries (Default: :code:`task_retry_interval` in manager blueprint Cloudify Manager Type for remote workflows and :code:`task_retry_interval` workflow configuration for local workflows).
        
        :rtype: int
        """

@allow_unknown_fields
@has_fields
@dsl_specification('interfaces-2', 'cloudify-1.1')
@dsl_specification('interfaces-2', 'cloudify-1.2')
@dsl_specification('interfaces-2', 'cloudify-1.3')
class InterfaceAssignment(InterfaceAssignment1_0):
    @object_dict_unknown_fields(OperationAssignment)
    def operations(self):
        """
        :rtype: dict of str, :class:`OperationAssignment`
        """

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

from .exceptions import UnknownInputError, MissingRequiredInputError
from aria_extension_cloudify.classic_modeling import add_deployment_plan_attributes
from aria_extension_cloudify.classic_modeling.post_processing import PostProcessingContext
from aria.utils import deepcopy_with_locators, string_list_as_string

def prepare_deployment_plan(plan, inputs=None, **kwargs):
    """
    Prepare a plan for deployment
    """
    
    #print '!!! prepare_deployment_plan', inputs, kwargs
    
    plan = deepcopy_with_locators(plan)
    add_deployment_plan_attributes(plan)
    
    if inputs:
        unknown_inputs = []
        for input_name, the_input in inputs.iteritems():
            if input_name in plan['inputs']:
                plan['inputs'][input_name]['value'] = deepcopy_with_locators(the_input)
            else:
                unknown_inputs.append(input_name)
        if unknown_inputs:
            raise UnknownInputError('unknown inputs specified: %s' % string_list_as_string(unknown_inputs))

    missing_inputs = []    
    for input_name, the_input in plan['inputs'].iteritems():
        if the_input.get('value') is None:
            the_input['value'] = the_input.get('default')
        if the_input.get('value') is None:
            missing_inputs.append(input_name)
    if missing_inputs:
        raise MissingRequiredInputError('inputs not specified: %s' % string_list_as_string(missing_inputs))
            
    # TODO: now that we have inputs, we should scan properties and inputs
    # and evaluate functions
    
    context = PostProcessingContext(plan, None, None, None, None)
    context.process(plan)
    
    return plan

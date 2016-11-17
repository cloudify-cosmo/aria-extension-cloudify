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

from ...v1_0.modeling.node_templates import Scalable, get_node_template_scalable as _get_node_template_scalable
from aria.validation import Issue
from aria.utils import safe_repr

def get_node_template_scalable(context, presentation):
    scalable = Scalable()
    
    found = False
    capabilities = presentation.capabilities
    if capabilities:
        for key in capabilities.iterkeys():
            if key != 'scalable':
                context.validation.report('node template "%s" has unsupported capability: %s' % (presentation._fullname, safe_repr(key)), locator=presentation._get_child_locator('capabilities', key), level=Issue.BETWEEN_FIELDS)

        capability = capabilities.get('scalable')
        if capability is not None:
            properties = capability.properties
            if properties:
                for key in properties.iterkeys():
                    if key not in ('default_instances', 'min_instances', 'max_instances'):
                        context.validation.report('"scalable" capability in node template "%s" has unsupported property: %s' % (presentation._fullname, safe_repr(key)), locator=capability._get_child_locator('properties', key), level=Issue.BETWEEN_FIELDS)
                
                default_instances = properties.get('default_instances')
                scalable.default_instances = default_instances.value if default_instances is not None else 1
                min_instances = properties.get('min_instances')
                scalable.min_instances = min_instances.value if min_instances is not None else 0
                max_instances = properties.get('max_instances')
                scalable.max_instances = max_instances.value if max_instances is not None else -1
                scalable.validate(context, presentation, capability._locator)
                found = True

    if not found:
        # Deprecated
        return _get_node_template_scalable(context, presentation)

    return scalable

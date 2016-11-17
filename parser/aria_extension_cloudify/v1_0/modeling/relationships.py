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

from .properties import get_inherited_property_definitions, get_assigned_and_defined_property_values
from aria.validation import Issue
from aria.utils import safe_repr

#
# RelationshipType
#

def get_relationship_inherited_property_definitions(context, presentation):
    properties = get_inherited_property_definitions(context, presentation, 'properties')
    
    definition = properties.get('connection_type')
    if definition is not None:
        default = definition.default
        if default not in ('all_to_all', 'all_to_one'):
            context.validation.report('"connection_type" property default is not "all_to_all" or "all_to_one" in relationship type "%s": %s' % (presentation._fullname, safe_repr(default)), locator=definition._locator, level=Issue.BETWEEN_FIELDS)
    
    return properties

#
# RelationshipTemplate
#

def get_relationship_assigned_and_defined_property_values(context, presentation):
    values = get_assigned_and_defined_property_values(context, presentation)

    if 'connection_type' in values:
        value = values['connection_type']
        if value.value not in ('all_to_all', 'all_to_one'):
            context.validation.report('"connection_type" property is not "all_to_all" or "all_to_one" in relationship in node template "%s": %s' % (presentation._container._fullname, safe_repr(value)), locator=presentation._get_child_locator('properties', 'connection_type'), level=Issue.BETWEEN_FIELDS)
    
    return values
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

from .data_types import coerce_value
from aria.validation import Issue
from aria.presentation import Value
from aria.utils import merge, deepcopy_with_locators
from collections import OrderedDict

#
# NodeType, RelationshipType, PolicyType, DataType
#

def get_inherited_property_definitions(context, presentation, field_name, for_presentation=None): # works on properties, parameters, inputs, and attributes
    """
    Returns our property definitions added on top of those of our parent, if we have one (recursively).
    
    Allows overriding all aspects of parent properties except data type.  
    """
    
    # Get definitions from parent
    parent = presentation._get_parent(context)
    definitions = get_inherited_property_definitions(context, parent, field_name, for_presentation=presentation) if parent is not None else OrderedDict()
    
    # Add/merge our definitions
    our_definitions = getattr(presentation, field_name)
    if our_definitions:
        our_definitions_clone = OrderedDict()
        for name, our_definition in our_definitions.iteritems():
            our_definitions_clone[name] = our_definition._clone(for_presentation)
        our_definitions = our_definitions_clone
        merge_property_definitions(context, presentation, definitions, our_definitions, field_name, for_presentation)
    
    for definition in definitions.itervalues():
        definition._reset_method_cache()
    
    return definitions

#
# NodeTemplate, RelationshipTemplate
#

def get_assigned_and_defined_property_values(context, presentation, field_name='properties'):
    """
    Returns the assigned property values while making sure they are defined in our type.
    
    The property definition's default value, if available, will be used if we did not assign it.
    
    Makes sure that required properties indeed end up with a value.
    """

    values = OrderedDict()
    
    the_type = presentation._get_type(context)
    assignments = getattr(presentation, field_name)
    definitions = the_type._get_properties(context) if the_type is not None else None

    # Fill in our assignments, but make sure they are defined
    if assignments:
        for name, value in assignments.iteritems():
            if (definitions is not None) and (name in definitions):
                definition = definitions[name]
                v = value.value

                # For data type values, merge into the default value (note: this is Cloudify behavior; in TOSCA these values are always replaced)
                default = definition.default
                if isinstance(v, dict) and isinstance(default, dict) and (context.presentation.get_from_dict('service_template', 'data_types', definition.type) is not None):
                    t = deepcopy_with_locators(default)
                    merge(t, v)
                    v = t
                elif v is None:
                    v = default

                values[name] = coerce_property_value(context, value, definition, v)
            else:
                context.validation.report('assignment to undefined property "%s" in "%s"' % (name, presentation._fullname), locator=value._locator, level=Issue.BETWEEN_TYPES)

    # Fill in defaults from the definitions
    if definitions:
        for name, definition in definitions.iteritems():
            if (values.get(name) is None) and (definition.default is not None):
                values[name] = coerce_property_value(context, presentation, definition, definition.default) 
    
    validate_required_values(context, presentation, values, definitions)
    
    return values

#
# TopologyTemplate
#

def get_parameter_values(context, presentation, field_name):
    values = OrderedDict()
    
    parameters = getattr(presentation, field_name)

    # Fill in defaults and values
    if parameters:
        for name, parameter in parameters.iteritems():
            if (values.get(name) is None):
                if hasattr(parameter, 'value') and (parameter.value is not None):
                    values[name] = coerce_property_value(context, presentation, parameter, parameter.value) # for parameters only 
                else:
                    default = parameter.default if hasattr(parameter, 'default') else None
                    values[name] = coerce_property_value(context, presentation, parameter, default)
    
    return values

#
# Utils
#

def validate_required_values(context, presentation, values, definitions):
    """
    Check if required properties have not been assigned.
    """
    
    if not definitions:
        return
    for name, definition in definitions.iteritems():
        if getattr(definition, 'required', False) and ((values is None) or (values.get(name) is None)):
            context.validation.report('required property "%s" is not assigned a value in "%s"' % (name, presentation._fullname), locator=presentation._get_child_locator('properties'), level=Issue.BETWEEN_TYPES)

def merge_property_definition_default(context, definition):
    the_type = definition._get_type(context)
    if the_type is None:
        return
    if not hasattr(the_type, '_get_properties'):
        # Not a complex data type
        return

    default = OrderedDict()

    properties = the_type._get_properties(context)
    for property_name, prop in properties.iteritems():
        default_value = prop.default
        if default_value is not None:
            default[property_name] = default_value
    
    if default:
        # Make sure we have a dict
        if 'default' not in definition._raw:
            definition._raw['default'] = OrderedDict()
        
        # Merge our default over the type's default
        if isinstance(definition._raw['default'], dict): 
            definition._raw['default'] = merge(default, definition._raw['default'])

def merge_raw_property_definition(context, presentation, raw_property_definition, our_property_definition, field_name, property_name):
    merge(raw_property_definition, our_property_definition._raw)

def merge_property_definitions(context, presentation, property_definitions, our_property_definitions, field_name, for_presentation):
    if not our_property_definitions:
        return
    for property_name, our_property_definition in our_property_definitions.iteritems():
        if property_name in property_definitions:
            property_definition = property_definitions[property_name]
            merge_raw_property_definition(context, presentation, property_definition._raw, our_property_definition, field_name, property_name)
        else:
            property_definitions[property_name] = our_property_definition
        merge_property_definition_default(context, our_property_definition)

def coerce_property_value(context, presentation, definition, value, aspect=None): # works on properties, inputs, and parameters
    the_type = definition._get_type(context) if hasattr(definition, '_get_type') else None
    value = coerce_value(context, presentation, the_type, value, aspect)
    if (the_type is not None) and hasattr(the_type, '_name'):
        type_name = the_type._name
    else:
        type_name = getattr(definition, 'type', None)
    description = getattr(definition, 'description', None)
    description = description.value if description is not None else None
    return Value(type_name, value, description)

def convert_property_definitions_to_values(context, presentation, definitions):
    values = OrderedDict()
    for name, definition in definitions.iteritems():
        default = definition.default
        values[name] = coerce_property_value(context, definition, definition, default)
    return values

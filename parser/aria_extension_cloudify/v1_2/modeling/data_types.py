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

from ...v1_0.modeling.data_types import coerce_value, get_primitive_data_type
from aria.validation import Issue
from aria.presentation import get_locator
from aria.utils import safe_repr
from collections import OrderedDict

#
# DataType
#

def coerce_data_type_value(context, presentation, data_type, value, aspect):
    """
    Handles the :code:`_coerce_data()` hook for complex data types.
    
    We return the assigned property values while making
    sure they are defined in our type. The property definition's default value, if available, will
    be used if we did not assign it. We also make sure that required definitions indeed end up with
    a value.
    """
    
    definitions = data_type._get_properties(context)
    if isinstance(value, dict):
        r = OrderedDict()

        # Fill in our values, but make sure they are defined
        for name, v in value.iteritems():
            if name in definitions:
                definition = definitions[name]
                definition_type = definition._get_type(context)
                r[name] = coerce_value(context, presentation, definition_type, v, aspect)
            else:
                context.validation.report('assignment to undefined property "%s" in type "%s" in "%s"' % (name, data_type._fullname, presentation._fullname), locator=get_locator(v, value, presentation), level=Issue.BETWEEN_TYPES)

        # Fill in defaults from the definitions, and check if required definitions have not been assigned
        for name, definition in definitions.iteritems():
            if (r.get(name) is None) and hasattr(definition, 'default') and (definition.default is not None):
                definition_type = definition._get_type(context)
                r[name] = coerce_value(context, presentation, definition_type, definition.default, 'default')
            
            if (aspect != 'default') and getattr(definition, 'required', False) and (r.get(name) is None):
                # Note that we do not validate this for default aspects
                context.validation.report('required property "%s" in type "%s" is not assigned a value in "%s"' % (name, data_type._fullname, presentation._fullname), locator=presentation._get_child_locator('definitions'), level=Issue.BETWEEN_TYPES)
        
        value = r
    else:
        context.validation.report('value of type "%s" is not a dict in "%s"' % (data_type._fullname, presentation._fullname), locator=get_locator(value, presentation), level=Issue.BETWEEN_TYPES)
        value = None
    
    return value

def validate_data_type_name(context, presentation):
    """
    Makes sure the complex data type's name is not that of a built-in type.
    """
    
    name = presentation._name
    if get_primitive_data_type(name) is not None:
        context.validation.report('data type name is that of a built-in type: %s' % safe_repr(name), locator=presentation._locator, level=Issue.BETWEEN_TYPES)

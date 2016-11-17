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

from ..modeling.data_types import get_primitive_data_type, get_container_data_type
from ..modeling.properties import coerce_value
from aria.presentation import report_issue_for_unknown_type
from aria.validation import Issue
from aria.utils import safe_repr

#
# PropertyDefinition
#

def data_type_validator(field, presentation, context):
    """
    Makes sure that the field refers to a valid data type, whether complex or primitive. 
    
    Used with the :func:`field_validator` decorator for the :code:`type` field in :class:`PropertyDefinition`.
    
    Extra behavior beyond validation: generated function returns true if field is a complex data type.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        # Test for circular definitions
        container_data_type = get_container_data_type(presentation)
        if (container_data_type is not None) and (container_data_type._name == value):
            context.validation.report('type of property "%s" creates a circular value hierarchy: %s' % (presentation._fullname, safe_repr(value)), locator=presentation._get_child_locator('type'), level=Issue.BETWEEN_TYPES)
        
        # Can be a complex data type
        if context.presentation.get_from_dict('service_template', 'data_types', value) is not None:
            return True
        # Can be a primitive data type
        if get_primitive_data_type(value) is None:
            report_issue_for_unknown_type(context, presentation, 'data type', field.name)

    return False

def data_value_validator(field, presentation, context):
    """
    Makes sure that the field contains a valid value according to data type and constraints.

    Used with the :func:`field_validator` decorator for the :code:`default` field in :class:`PropertyDefinition`.
    """

    field.default_validate(presentation, context)

    value = getattr(presentation, field.name)
    if value is not None:
        the_type = presentation._get_type(context)
        coerce_value(context, presentation, the_type, value, field.name)

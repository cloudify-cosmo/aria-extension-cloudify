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

from .properties import coerce_property_value, convert_property_definitions_to_values
from aria.validation import Issue
from aria.presentation import get_locator
from aria.utils import merge, deepcopy_with_locators
from collections import OrderedDict

#
# NodeType, RelationshipType
#

def get_inherited_interface_definitions(context, presentation, type_name, field_name, for_presentation=None):
    """
    Returns our interface definitions added on top of those of our parent, if we have one (recursively).
    
    Allows overriding all aspects of parent interfaces except interface and operation input data types.  
    """
    
    # Get interfaces from parent
    parent = presentation._get_parent(context)
    interfaces = get_inherited_interface_definitions(context, parent, type_name, field_name, presentation) if parent is not None else OrderedDict()

    # Add/merge our interfaces
    our_interfaces = getattr(presentation, field_name)
    merge_interface_definitions(context, interfaces, our_interfaces, presentation, for_presentation=for_presentation)
    
    return interfaces

#
# NodeTemplate, RelationshipTemplate
#

def get_template_interfaces(context, presentation, type_name, field_name, fn_name):
    """
    Returns the assigned interface_template values. This includes the interfaces themselves, their
    operations, and inputs for operations.
    
    Operation inputs' default values, if available, will be used if we did not assign them.
    
    Makes sure that required inputs indeed end up with a value.
    
    This code is especially complex due to the many levels of nesting involved.
    """
    
    template_interfaces = OrderedDict()
    
    the_type = presentation._get_type(context) # NodeType, RelationshipType
    interface_definitions = getattr(the_type, fn_name)(context) if the_type is not None else None # InterfaceDefinition

    # Copy over interfaces from the type (will initialize inputs with default values)
    if interface_definitions is not None:
        for interface_name, interface_definition in interface_definitions.iteritems():
            # Note that in the case of a RelationshipTemplate, we will already have the values as InterfaceAssignment.
            # It will not be converted, just cloned.
            template_interfaces[interface_name] = convert_interface_definition_from_type_to_template(context, interface_definition, presentation)
    
    # Fill in our interfaces
    our_interface_assignments = getattr(presentation, field_name)
    if our_interface_assignments:
        for interface_name, our_interface_assignment in our_interface_assignments.iteritems(): # InterfaceAssignment
            if interface_name in template_interfaces:
                interface_assignment = template_interfaces[interface_name] # InterfaceAssignment
                interface_definition = interface_definitions[interface_name] # InterfaceDefinition
                merge_interface(context, presentation, interface_assignment, our_interface_assignment, interface_definition, interface_name) 
            else:
                # Unlike TOSCA, Cloudify lets you implement undeclared interfaces
                interface_assignment = our_interface_assignment._clone()
                coerce_inputs(context, presentation, interface_assignment, interface_name)
                template_interfaces[interface_name] = interface_assignment

    # Check that there are no required inputs that we haven't assigned
    for interface_name, interface_template in template_interfaces.iteritems():
        if interface_name in interface_definitions:
            interface_definition = interface_definitions[interface_name] # InterfaceDefinition
            our_interface_assignment = our_interface_assignments.get(interface_name) if our_interface_assignments is not None else None
            validate_required_interface_inputs(context, presentation, interface_template, interface_definition, our_interface_assignment, interface_name)
    
    return template_interfaces

#
# Utils
#

def convert_interface_definition_from_type_to_template(context, presentation, container):
    cls = context.presentation.presenter.INTERFACE_ASSIGNMENT_CLASS

    if isinstance(presentation, cls):
        # Nothing to convert, so just clone
        return presentation._clone(container)
    
    raw = convert_interface_definition_from_type_to_raw_template(context, presentation)
    return cls(name=presentation._name, raw=raw, container=container)

def convert_interface_definition_from_type_to_raw_template(context, presentation):
    raw = OrderedDict()
    
    # Copy operations
    operations = presentation.operations
    if operations:
        for operation_name, operation in operations.iteritems():
            raw[operation_name] = OrderedDict()
            implementation = operation.implementation
            if implementation is not None:
                raw[operation_name]['implementation'] = deepcopy_with_locators(implementation)
            executor = operation.executor
            if executor is not None:
                raw[operation_name]['executor'] = deepcopy_with_locators(executor)
            if hasattr(operation, 'max_retries'): # Introduced in DSL v1.1
                max_retries = operation.max_retries
                if max_retries is not None:
                    raw[operation_name]['max_retries'] = deepcopy_with_locators(max_retries)
                retry_interval = operation.retry_interval
                if retry_interval is not None:
                    raw[operation_name]['retry_interval'] = deepcopy_with_locators(retry_interval)
            inputs = operation.inputs
            if inputs is not None:
                raw[operation_name]['inputs'] = convert_property_definitions_to_values(context, presentation, inputs)
    
    return raw

def merge_interface(context, presentation, interface_assignment, our_interface_assignment, interface_definition, interface_name):
    # Assign operation implementations and inputs
    our_operation_templates = our_interface_assignment.operations # OperationAssignment
    operation_definitions = interface_definition._get_operations(context) if hasattr(interface_definition, '_get_operations') else interface_definition.operations # OperationDefinition or OperationAssignment
    if our_operation_templates:
        for operation_name, our_operation_template in our_operation_templates.iteritems(): # OperationAssignment
            operation_definition = operation_definitions.get(operation_name) # OperationDefinition

            our_input_assignments = our_operation_template.inputs
            our_implementation = our_operation_template.implementation
            
            if (our_input_assignments is not None) or (our_implementation is not None):
                # Make sure we have the dict
                if (operation_name not in interface_assignment._raw) or (interface_assignment._raw[operation_name] is None):
                    interface_assignment._raw[operation_name] = OrderedDict()
            
            if our_implementation is not None:
                interface_assignment._raw[operation_name]['implementation'] = deepcopy_with_locators(our_implementation)
            our_executor = our_operation_template.executor
            if our_executor is not None:
                interface_assignment._raw[operation_name]['executor'] = deepcopy_with_locators(our_executor)
            if hasattr(our_operation_template, 'max_retries'): # Introduced in DSL v1.1
                our_max_retries = our_operation_template.max_retries
                if our_max_retries is not None or our_implementation is not None:
                    interface_assignment._raw[operation_name]['max_retries'] = deepcopy_with_locators(our_max_retries)
                our_retry_interval = our_operation_template.retry_interval
                if our_retry_interval is not None or our_implementation is not None:
                    interface_assignment._raw[operation_name]['retry_interval'] = deepcopy_with_locators(our_retry_interval)

            # Assign/merge operation inputs
            input_definitions = operation_definition.inputs if operation_definition is not None else None
            assign_raw_inputs(context, interface_assignment._raw[operation_name], our_input_assignments, input_definitions, interface_name, operation_name, presentation)

def merge_raw_input_definition(context, the_raw_input, our_input, interface_name, operation_name, presentation, type_name):
    # Check if we changed the type
    # TODO: allow a sub-type?
    input_type1 = the_raw_input.get('type')
    input_type2 = our_input.type
    if input_type1 != input_type2:
        if operation_name is not None:
            context.validation.report('interface %s "%s" changes operation input "%s.%s" type from "%s" to "%s" in "%s"' % (type_name, interface_name, operation_name, our_input._name, input_type1, input_type2, presentation._fullname), locator=input_type2._locator, level=Issue.BETWEEN_TYPES)
        else:
            context.validation.report('interface %s "%s" changes input "%s" type from "%s" to "%s" in "%s"' % (type_name, interface_name, our_input._name, input_type1, input_type2, presentation._fullname), locator=input_type2._locator, level=Issue.BETWEEN_TYPES)

    # Merge    
    merge(the_raw_input, our_input._raw)

def merge_raw_input_definitions(context, raw_inputs, our_inputs, interface_name, operation_name, presentation, type_name):
    for input_name, our_input in our_inputs.iteritems():
        if input_name in raw_inputs:
            merge_raw_input_definition(context, raw_inputs[input_name], our_input, interface_name, operation_name, presentation, type_name)
        else:
            raw_inputs[input_name] = deepcopy_with_locators(our_input._raw)

def merge_raw_operation_definition(context, raw_operation, our_operation, interface_name, presentation, type_name):
    if not isinstance(our_operation._raw, dict):
        # Convert short form to long form
        raw_operation['implementation'] = deepcopy_with_locators(our_operation._raw)
        return

    # Add/merge inputs
    our_operation_inputs = our_operation.inputs
    if our_operation_inputs:
        # Make sure we have the dict
        if ('inputs' not in raw_operation) or (raw_operation.get('inputs') is None):
            raw_operation['inputs'] = OrderedDict()
            
        merge_raw_input_definitions(context, raw_operation['inputs'], our_operation_inputs, interface_name, our_operation._name, presentation, type_name)
    
    # Overrides
    if our_operation._raw.get('implementation') is not None:
        raw_operation['implementation'] = deepcopy_with_locators(our_operation._raw['implementation'])
    if our_operation._raw.get('executor') is not None:
        raw_operation['executor'] = deepcopy_with_locators(our_operation._raw['executor'])
    if our_operation._raw.get('max_retries') is not None:
        raw_operation['max_retries'] = deepcopy_with_locators(our_operation._raw['max_retries'])
    if our_operation._raw.get('retry_interval') is not None:
        raw_operation['retry_interval'] = deepcopy_with_locators(our_operation._raw['retry_interval'])

def merge_raw_operation_definitions(context, raw_operations, our_operations, interface_name, presentation, type_name):
    for operation_name, our_operation in our_operations.iteritems():
        if operation_name in raw_operations:
            raw_operation = raw_operations[operation_name]
            if isinstance(raw_operation, basestring):
                # Convert short form to long form
                raw_operations[operation_name] = OrderedDict((('implementation', raw_operation),))
                raw_operation = raw_operations[operation_name]
            merge_raw_operation_definition(context, raw_operation, our_operation, interface_name, presentation, type_name)
        else:
            raw_operations[operation_name] = deepcopy_with_locators(our_operation._raw)

def merge_interface_definition(context, interface, our_source, presentation, type_name):
    # Add/merge operations
    our_operations = our_source.operations
    if our_operations:
        merge_raw_operation_definitions(context, interface._raw, our_operations, our_source._name, presentation, type_name)

def merge_interface_definitions(context, interfaces, our_interfaces, presentation, for_presentation=None):
    if not our_interfaces:
        return
    for name, our_interface in our_interfaces.iteritems():
        if name in interfaces:
            merge_interface_definition(context, interfaces[name], our_interface, presentation, 'definition')
        else:
            interfaces[name] = our_interface._clone(for_presentation)

def assign_raw_inputs(context, values, assignments, definitions, interface_name, operation_name, presentation):
    if not assignments:
        return

    # Make sure we have the dict
    if ('inputs' not in values) or (values['inputs'] is None):
        values['inputs'] = OrderedDict()

    # Assign inputs
    for input_name, assignment in assignments.iteritems():
        if (definitions is not None) and (input_name not in definitions):
            if operation_name is not None:
                context.validation.report('interface definition "%s" assigns a value to an unknown operation input "%s.%s" in "%s"' % (interface_name, operation_name, input_name, presentation._fullname), locator=assignment._locator, level=Issue.BETWEEN_TYPES)
            else:
                context.validation.report('interface definition "%s" assigns a value to an unknown input "%s" in "%s"' % (interface_name, input_name, presentation._fullname), locator=assignment._locator, level=Issue.BETWEEN_TYPES)

        definition = definitions.get(input_name) if definitions is not None else None

        # Note: default value has already been assigned 
        
        # Coerce value
        values['inputs'][input_name] = coerce_property_value(context, assignment, definition, assignment.value)

def coerce_inputs(context, presentation, interface_assignment, interface_name):
    operations = interface_assignment.operations
    if operations:
        for operation_name, operation in operations.iteritems():
            assignments = operation.inputs
            if assignments:
                for input_name, assignment in assignments.iteritems():
                    interface_assignment._raw[operation_name]['inputs'][input_name] = coerce_property_value(context, assignment, None, assignment.value)
                    interface_assignment._reset_method_cache()

def validate_required_inputs(context, presentation, assignment, definition, original_assignment, interface_name, operation_name):
    input_definitions = definition.inputs
    if input_definitions:
        for input_name, input_definition in input_definitions.iteritems():
            if getattr(input_definition, 'required', False):
                prop = assignment.inputs.get(input_name) if ((assignment is not None) and (assignment.inputs is not None)) else None
                value = prop.value if prop is not None else None
                value = value.value if value is not None else None
                if value is None:
                    context.validation.report('interface definition "%s" does not assign a value to a required operation input "%s.%s" in "%s"' % (interface_name, operation_name, input_name, presentation._fullname), locator=get_locator(original_assignment, presentation), level=Issue.BETWEEN_TYPES)

def validate_required_interface_inputs(context, presentation, assignment, definition, original_assignment, interface_name):
    assignment_operations = assignment.operations 
    operation_definitions = definition.operations
    if operation_definitions:
        for operation_name, operation_definition in operation_definitions.iteritems():
            assignment_operation = assignment_operations.get(operation_name) if assignment_operations is not None else None
            original_operation = original_assignment.operations.get(operation_name, original_assignment) if (original_assignment is not None and original_assignment.operations is not None) else original_assignment
            validate_required_inputs(context, presentation, assignment_operation, operation_definition, original_operation, interface_name, operation_name)

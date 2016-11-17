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

from aria import InvalidValueError, dsl_specification
from aria.validation import Issue
from aria.modeling import Function, CannotEvaluateFunctionException
from aria.utils import as_raw, safe_repr

@dsl_specification('intrinsic-functions-2', 'cloudify-1.0')
@dsl_specification('intrinsic-functions-2', 'cloudify-1.1')
@dsl_specification('intrinsic-functions-2', 'cloudify-1.2')
@dsl_specification('intrinsic-functions-2', 'cloudify-1.3')
class GetInput(Function):
    """
    :code:`get_input` is used for referencing :code:`inputs` described in the inputs section of the blueprint. :code:`get_input` can be used in node properties, outputs, and node/relationship operation inputs. The function is evaluated on deployment creation.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-intrinsic-functions/>`__.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator
        
        self.input_property_name = parse_string_expression(context, presentation, 'get_input', None, 'the input property name', argument)

        if isinstance(self.input_property_name, basestring):
            the_input = context.presentation.get_from_dict('service_template', 'inputs', self.input_property_name)
            if the_input is None:
                raise InvalidValueError('function "get_input" argument is not a valid input name: %s' % safe_repr(argument), locator=self.locator)
        
        self.context = context

    @property
    def as_raw(self):
        return {'get_input': as_raw(self.input_property_name)}
    
    def _evaluate(self, context, container):
        raise CannotEvaluateFunctionException()

@dsl_specification('intrinsic-functions-3', 'cloudify-1.0')
@dsl_specification('intrinsic-functions-3', 'cloudify-1.1')
@dsl_specification('intrinsic-functions-3', 'cloudify-1.2')
@dsl_specification('intrinsic-functions-3', 'cloudify-1.3')
class GetProperty(Function):
    """
    :code:`get_property` is used for referencing node properties within the blueprint. :code:`get_property` can be used in node properties, outputs, and node/relationship operation inputs. The function is evaluated on deployment creation.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-intrinsic-functions/>`__.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator
        
        if (not isinstance(argument, list)) or (len(argument) < 2):
            raise InvalidValueError('function "get_property" argument must be a list of at least 2 string expressions: %s' % safe_repr(argument), locator=self.locator)

        self.modelable_entity_name = parse_modelable_entity_name(context, presentation, 'get_property', 0, argument[0])
        self.nested_property_name_or_index = argument[1:] # the first of these will be tried as a req-or-cap name

    @property
    def as_raw(self):
        return {'get_property': [self.modelable_entity_name] + self.nested_property_name_or_index}

    def _evaluate(self, context, container):
        raise CannotEvaluateFunctionException()

@dsl_specification('intrinsic-functions-4', 'cloudify-1.0')
@dsl_specification('intrinsic-functions-4', 'cloudify-1.1')
@dsl_specification('intrinsic-functions-4', 'cloudify-1.2')
@dsl_specification('intrinsic-functions-4', 'cloudify-1.3')
class GetAttribute(Function):
    """
    :code:`get_attribute` is used to reference runtime-properties of different node-instances from within the blueprint.
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-intrinsic-functions/>`__.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator
        
        if (not isinstance(argument, list)) or (len(argument) < 2):
            raise InvalidValueError('function "get_attribute" argument must be a list of at least 2 string expressions: %s' % safe_repr(argument), locator=self.locator)

        self.modelable_entity_name = parse_modelable_entity_name(context, presentation, 'get_attribute', 0, argument[0])
        self.nested_property_name_or_index = argument[1:] # the first of these will be tried as a req-or-cap name

    @property
    def as_raw(self):
        return {'get_attribute': [self.modelable_entity_name] + self.nested_property_name_or_index}

    def _evaluate(self, context, container):
        raise CannotEvaluateFunctionException()

#
# Utils
#

def get_function(context, presentation, value):
    functions = context.presentation.presenter.functions
    if isinstance(value, dict) and (len(value) == 1):
        key = value.keys()[0]
        if key in functions:
            try:
                return True, functions[key](context, presentation, value[key])
            except InvalidValueError as e:
                context.validation.report(issue=e.issue)
                return True, None
    return False, None

def parse_string_expression(context, presentation, name, index, explanation, value):
    is_function, fn = get_function(context, presentation, value)
    if is_function:
        return fn
    else:
        value = str(value)
    return value

def parse_modelable_entity_name(context, presentation, name, index, value):
    value = parse_string_expression(context, presentation, name, index, 'the modelable entity name', value)
    if value == 'SELF':
        the_self, _ = parse_self(presentation)
        if the_self is None:
            raise invalid_modelable_entity_name(name, index, value, presentation._locator, 'a node template or a relationship template')
    elif value == 'HOST':
        _, self_variant = parse_self(presentation)
        if self_variant not in ('node_template', 'fake'):
            raise invalid_modelable_entity_name(name, index, value, presentation._locator, 'a node template')
    elif (value == 'SOURCE') or (value == 'TARGET'):
        _, self_variant = parse_self(presentation)
        if self_variant not in ('relationship_template', 'fake'):
            raise invalid_modelable_entity_name(name, index, value, presentation._locator, 'a relationship template')
    elif isinstance(value, basestring):
        if context.presentation.presenter is not None:
            node_templates = context.presentation.get('service_template', 'node_templates') or {}
            relationship_templates = context.presentation.get('service_template', 'relationships') or {}
            if (value not in node_templates) and (value not in relationship_templates):
                raise InvalidValueError('function "%s" parameter %d is not a valid modelable entity name: %s' % (name, index + 1, safe_repr(value)), locator=presentation._locator, level=Issue.BETWEEN_TYPES)
    return value

def parse_self(presentation):
    from .templates import NodeTemplate, RelationshipTemplate
    from .types import NodeType, RelationshipType
    
    if presentation is None:
        return None, None    
    elif isinstance(presentation, NodeTemplate) or isinstance(presentation, NodeType):
        return presentation, 'node_template'
    elif isinstance(presentation, RelationshipTemplate) or isinstance(presentation, RelationshipType):
        return presentation, 'relationship_template'
    else:
        return parse_self(presentation._container)

def invalid_modelable_entity_name(name, index, value, locator, contexts):
    return InvalidValueError('function "%s" parameter %d can be "%s" only in %s' % (name, index + 1, value, contexts), locator=locator, level=Issue.FIELD)

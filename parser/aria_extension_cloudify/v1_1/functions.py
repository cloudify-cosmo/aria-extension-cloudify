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

from ..v1_0.functions import parse_string_expression
from aria import InvalidValueError, dsl_specification
from aria.modeling import Function, CannotEvaluateFunctionException
from aria.utils import FrozenList, as_raw, safe_repr

@dsl_specification('intrinsic-functions-1', 'cloudify-1.1')
@dsl_specification('intrinsic-functions-1', 'cloudify-1.2')
@dsl_specification('intrinsic-functions-1', 'cloudify-1.3')
class Concat(Function):
    """
    :code:`concat` is used for concatenating strings in different sections of the blueprint. :code:`concat` can be used in node properties, outputs, and node/relationship operation inputs. The function is evaluated once on deployment creation which will replace :code:`get_input` and :code:`get_property` usages; and it is evaluated on every operation execution and outputs evaluation, to replace usages of :code:`get_attribute` (if there are any).
    
    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-intrinsic-functions/>`__.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator
        
        if not isinstance(argument, list):
            raise InvalidValueError('function "concat" argument must be a list of string expressions: %s' % safe_repr(argument), locator=self.locator)
        
        string_expressions = []
        for index in range(len(argument)):
            string_expressions.append(parse_string_expression(context, presentation, 'concat', index, None, argument[index]))
        self.string_expressions = FrozenList(string_expressions)    

    @property
    def as_raw(self):
        string_expressions = []
        for string_expression in self.string_expressions:
            if hasattr(string_expression, 'as_raw'):
                string_expression = as_raw(string_expression)
            string_expressions.append(string_expression)
        return {'concat': string_expressions}

    def _evaluate(self, context, container):
        raise CannotEvaluateFunctionException()

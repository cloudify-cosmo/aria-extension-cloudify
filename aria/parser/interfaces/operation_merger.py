# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ..constants import LOCAL_AGENT
from .utils import operation_mapping, merge_schema_and_instance_inputs


NO_OP = operation_mapping()


class OperationMerger(object):  # pylint: disable=too-few-public-methods
    def __init__(self, overriding_operation, overridden_operation):
        self._create_operation_handlers = {
            str: self._create_operation_from_string,
            dict: self._create_operation_from_dict,
        }
        self.overriding_operation = self._create_operation(overriding_operation)
        self.overridden_operation = self._create_operation(overridden_operation)

    def merge(self):
        raise NotImplementedError('Must be implemented by subclasses')

    def _create_operation_from_string(self, raw_operation):
        return operation_mapping(
            implementation=raw_operation,
            inputs={},
            executor=LOCAL_AGENT,
            max_retries=None,
            retry_interval=None)

    def _create_operation_from_dict(self, raw_operation):
        return operation_mapping(**raw_operation)

    def _create_operation(self, raw_operation):
        if raw_operation is None:
            return None
        return self._create_operation_handlers[type(raw_operation)](raw_operation)


class NodeTemplateNodeTypeOperationMerger(OperationMerger):  # pylint: disable=too-few-public-methods
    def merge(self):
        if self.overridden_operation is None:
            # the operation is not defined in the type
            # should be merged by the node template operation
            return self.overriding_operation
        if self.overriding_operation is None:
            # the operation is not defined in the template
            # should be merged by the node type operation
            # this will validate that all schema inputs have
            # default values
            return operation_mapping(
                implementation=self.overridden_operation['implementation'],
                inputs=merge_schema_and_instance_inputs(
                    schema_inputs=self.overridden_operation['inputs'],
                    instance_inputs={}),
                executor=self.overridden_operation['executor'],
                max_retries=self.overridden_operation['max_retries'],
                retry_interval=self.overridden_operation['retry_interval'])
        if self.overriding_operation == NO_OP:
            # no-op overrides
            return NO_OP
        if self.overridden_operation == NO_OP:
            # no-op overridden
            return self.overriding_operation
        merged_operation_implementation = self._derive_implementation()
        return operation_mapping(
            implementation=merged_operation_implementation,
            inputs=self._derive_inputs(merged_operation_implementation),
            executor=self._derive_executor(merged_operation_implementation),
            max_retries=self._derive_max_retries(merged_operation_implementation),
            retry_interval=self._derive_retry_interval(merged_operation_implementation))

    def _derive_implementation(self):
        return (self.overriding_operation['implementation']
                or self.overridden_operation['implementation'])

    def _derive_inputs(self, merged_operation_implementation):
        if merged_operation_implementation == self.overridden_operation['implementation']:
            # this means the node template inputs should adhere to
            # the node type inputs schema (since its the same implementation)
            return merge_schema_and_instance_inputs(
                schema_inputs=self.overridden_operation['inputs'],
                instance_inputs=self.overriding_operation['inputs'])
        # the node template implementation overrides
        # the node type implementation. this means
        # we take the inputs defined in the node template
        return self.overriding_operation['inputs']

    def _derive_executor(self, merged_operation_implementation):
        return self._derive_with_impl('executor', merged_operation_implementation)

    def _derive_max_retries(self, merged_operation_implementation):
        return self._derive_with_impl('max_retries', merged_operation_implementation)

    def _derive_retry_interval(self, merged_operation_implementation):
        return self._derive_with_impl('retry_interval', merged_operation_implementation)

    def _derive_with_impl(self, field_name, merged_operation_implementation):
        node_template_operation_value = self.overriding_operation[field_name]
        if merged_operation_implementation != self.overridden_operation['implementation']:
            # this means the node template operation value will take
            # precedence (even if it is None, in which case,
            # the default value will apply (plugin for executor, and global
            # config for retry params)
            return node_template_operation_value
        if node_template_operation_value is not None:
            # node template operation value is declared
            # explicitly, use it
            return node_template_operation_value
        return self.overridden_operation[field_name]


class NodeTypeNodeTypeOperationMerger(OperationMerger):  # pylint: disable=too-few-public-methods
    def merge(self):
        if self.overriding_operation is None:
            return self.overridden_operation
        return self.overriding_operation


RelationshipTypeRelationshipTypeOperationMerger = NodeTypeNodeTypeOperationMerger
RelationshipTypeRelationshipInstanceOperationMerger = NodeTemplateNodeTypeOperationMerger

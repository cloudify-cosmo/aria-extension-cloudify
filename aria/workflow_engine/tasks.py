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

import json
from datetime import datetime

import jsonpickle
from luigi import Task, WrapperTask
from luigi import Parameter, TaskParameter

from ..events import (
    signal,
    start_task_signal,
    end_task_signal,
    on_success_task_signal,
    on_failure_task_signal,

    start_workflow_signal,
    end_workflow_signal,
    start_sub_workflow_signal,
    end_sub_workflow_signal,
    start_operation_signal,
    end_operation_signal,
    on_success_operation_signal,
    on_failure_operation_signal,
)
from ..storage.drivers import StorageError
from . import executors


class TaskListParameter(TaskParameter):
    def parse(self, tasks):
        return [
            super(TaskListParameter, self).parse(task)
            for task in tasks
        ]

    def serialize(self, cls_list):
        return json.dumps([
            super(TaskListParameter, self).serialize(cls)
            for cls in cls_list
        ])


class ContextParameter(Parameter):
    def parse(self, context_json):
        return jsonpickle.loads(context_json)

    def serialize(self, context):
        return jsonpickle.dumps(context)


class EngineBaseTask(Task):
    task_namespace = 'workflow'
    task_name = Parameter(
        description='Task Name',
        positional=False,
        always_in_help=True,
    )
    context = ContextParameter(
        description='Task context object with all context related API',
        positional=False,
        always_in_help=True,
    )
    depends_on = TaskListParameter(
        description='The operations and sub-workflows that this workflow depends on',
        positional=False,
        always_in_help=True,
        default=(),
    )
    start_signal_name = Parameter(
        description='start task signal name',
        positional=False,
        always_in_help=True,
        default=start_task_signal.name,
    )
    end_signal_name = Parameter(
        description='end task signal name',
        positional=False,
        always_in_help=True,
        default=end_task_signal.name,
    )
    on_success_signal_name = Parameter(
        description='success task signal name',
        positional=False,
        always_in_help=True,
        default=on_success_task_signal.name,
    )
    on_failure_signal_name = Parameter(
        description='failure task signal name',
        positional=False,
        always_in_help=True,
        default=on_failure_task_signal.name,
    )

    def __init__(self, *args, **kwargs):
        super(EngineBaseTask, self).__init__(*args, **kwargs)
        self.start_signal = signal(self.start_signal_name)
        self.end_signal = signal(self.end_signal_name)
        self.on_success_signal = signal(self.on_success_signal_name)
        self.on_failure_signal = signal(self.on_failure_signal_name)

    def __repr__(self):
        return '{task_type}(name={task_name})'.format(
            task_type=self.__class__.__name__,
            task_name=self.task_name)

    def run(self):
        self.start_signal.send(self)
        try:
            self.execute()
        finally:
            self.end_signal.send(self)

    def execute(self):
        """
        method to implement in sub class
        """
        pass

    def on_success(self):
        self.on_success_signal.send(self)

    def on_failure(self, exception):
        try:
            self.on_failure_signal.send(self, exception=exception)
        except:
            self.context.logger.debug('task on_failure handler failed', exc_info=True)
        return super(EngineBaseTask, self).on_failure(exception)


class EngineWrapperTask(EngineBaseTask, WrapperTask):
    task_namespace = 'workflow'

    def requires(self):
        """
        The operations and sub-workflows that this task depends on.
        """
        for task in self.depends_on:
            yield task


class StartWorkflowTask(EngineBaseTask):
    start_signal_name = Parameter(
        description='start workflow signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=start_workflow_signal.name,
    )

    def __init__(self, *args, **kwargs):
        super(StartWorkflowTask, self).__init__(*args, **kwargs)
        self.start_signal.connect(self._create_execution_in_storage, sender=self)

    def complete(self):
        try:
            self.context.execution
        except StorageError:
            return False
        return True

    def _create_execution_in_storage(self, *args, **kwargs):
        Execution = self.context.storage.execution.model_cls
        execution = Execution(
            id=self.context.execution_id,
            deployment_id=self.context.deployment_id,
            workflow_id=self.context.workflow_id,
            blueprint_id=self.context.blueprint_id,
            status=Execution.STARTED,
            created_at=datetime.utcnow(),
            error='',
            parameters=self.context.parameters,
            is_system_workflow=False
        )
        self.context.execution = execution


class EndWorkflowTask(EngineWrapperTask):
    on_success_signal_name = Parameter(
        description='End workflow signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=end_workflow_signal.name,
    )

    def __init__(self, *args, **kwargs):
        super(EndWorkflowTask, self).__init__(*args, **kwargs)
        self.on_success_signal.connect(
            self._update_execution_in_storage_to_finished,
            sender=self)

    def complete(self):
        try:
            execution = self.context.execution
        except StorageError:
            return False
        return (
            execution.status in execution.END_STATES
            and super(EndWorkflowTask, self).complete())

    def _update_execution_in_storage_to_finished(self, *args, **kwargs):
        execution = self.context.execution
        execution.status = execution.TERMINATED
        self.context.execution = execution


class StartSubWorkflowTask(EngineWrapperTask):
    start_signal_name = Parameter(
        description='Start sub workflow signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=start_sub_workflow_signal.name,
    )


class EndSubWorkflowTask(EngineWrapperTask):
    on_success_signal_name = Parameter(
        description='End sub workflow signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=end_sub_workflow_signal.name,
    )


class OperationTask(EngineWrapperTask):
    executor_name = Parameter(
        description='The name of the executor that will run the operation',
        positional=False,
        always_in_help=True,
        significant=False,
        default='OperationStoryteller',
    )
    start_signal_name = Parameter(
        description='Start operation signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=start_operation_signal.name,
    )
    end_signal_name = Parameter(
        description='End operation signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=end_operation_signal.name,
    )
    on_success_signal_name = Parameter(
        description='Success operation signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=on_success_operation_signal.name,
    )
    on_failure_signal_name = Parameter(
        description='Failure operation signal name',
        positional=False,
        always_in_help=True,
        significant=False,
        default=on_failure_operation_signal.name,
    )

    def __init__(self, *args, **kwargs):
        super(OperationTask, self).__init__(*args, **kwargs)
        self.skip_on_failure = kwargs.pop('skip_on_failure', False)
        self.operation_executor = executors[self.executor_name]

        self.start_signal.connect(self._change_state_to_start, sender=self)
        self.on_success_signal.connect(self._update_operation_to_success, sender=self)
        self.on_failure_signal.connect(self._update_operation_on_failure, sender=self)

    def execute(self):
        """
        Operation executor
        """
        executor = self.operation_executor(context=self.context, handler_path='')
        executor.start()

    def complete(self):
        try:
            operation = self.context.operation
        except StorageError:
            return False
        return operation.finished and not operation.need_to_retry

    def _change_state_to_start(self, *args, **kwargs):
        Operation = self.context.storage.operation.model_cls
        operation = Operation(
            id=self.context.id,
            execution_id=self.context.execution_id,
            max_retries=self.context.parameters.get('max_retries', 1),
            started_at=datetime.utcnow(),
            status=Operation.STARTED,
        )
        self.context.operation = operation

    def _update_operation_to_success(self, *args, **kwargs):
        operation = self.context.operation
        operation.status = operation.SUCCESS
        operation.ended_at = datetime.utcnow()
        self.context.operation = operation

    def _update_operation_on_failure(self, *args, **kwargs):
        operation = self.context.operation
        operation.ended_at = datetime.utcnow()
        operation.status = operation.FAILED
        self.context.operation = operation

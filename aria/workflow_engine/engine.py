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

"""
Create Engine wrapper on Luigi workflow engine
"""

import os
from collections import OrderedDict
from multiprocessing import cpu_count

import luigi

from ..logger import LoggerMixin
from ..tasks_graph import TaskGraph
from ..contexts import OperationContext
from .tasks import (
    StartWorkflowTask,
    EndWorkflowTask,
    StartSubWorkflowTask,
    EndSubWorkflowTask,
    OperationTask,
)


class Engine(LoggerMixin):
    def __init__(self, concurrency_count=cpu_count(), **kwargs):
        super(Engine, self).__init__(**kwargs)
        self.concurrency_count = concurrency_count
        self.workflow_tasks = OrderedDict()
        self.failed = None
        self.engine_logger_conf = os.path.join(
            os.path.dirname(__file__), 'luigi_logger.conf')

        self._end_task_name = 'Ending.{0}'.format
        self._start_task_name = 'Starting.{0}'.format

    @property
    def workflow_task(self):
        """
        :return: the primary task of the workflow
        """
        return next(reversed(self.workflow_tasks.values()))

    def create_workflow(
            self,
            workflow_context,
            graph,
            task_start_cls=StartWorkflowTask,
            task_end_cls=EndWorkflowTask,
            depends_on=()):
        """
        Creates a workflow based on the workflow context and the task-graph.
        :param WorkflowContext workflow_context:
        :param TaskGraph graph: graph that define the workflow with
                                operation context and sub graphs
        :param task_start_cls: the class of the start task.
                               should be StartSubWorkflowTask for sub-workflow,
                               or StartWorkflowTask for the workflow
        :param task_end_cls: the class of the end task.
                             should be EndSubWorkflowTask for sub-workflow,
                             or EndWorkflowTask for the workflow
        :param depends_on: the dependencies of the current workflow.
        """
        workflow_start_task = task_start_cls(
            task_name=self._start_task_name(graph.name),
            depends_on=depends_on,
            context=workflow_context)
        self.workflow_tasks[self._start_task_name(graph.name)] = workflow_start_task

        for operation_or_workflow, dependencies in graph.task_tree(reverse=True):
            operation_dependencies = self._get_tasks_from_dependencies(
                dependencies, default_dependencies=[workflow_start_task])

            if self._is_operation(operation_or_workflow):
                operation_context = operation_or_workflow
                operation_task = OperationTask(
                    task_name=operation_context.name,
                    context=operation_context,
                    depends_on=operation_dependencies,
                    **operation_context.engine_options)
                self.workflow_tasks[operation_context.name] = operation_task
            else:
                self.create_workflow(
                    graph=operation_or_workflow,
                    workflow_context=workflow_context,
                    task_start_cls=StartSubWorkflowTask,
                    task_end_cls=EndSubWorkflowTask,
                    depends_on=operation_dependencies)

        workflow_dependencies = self._get_tasks_from_dependencies(
            graph.leaf_tasks, default_dependencies=[workflow_start_task])
        workflow_end_task = task_end_cls(
            task_name=self._end_task_name(graph.name),
            context=workflow_context,
            depends_on=workflow_dependencies)
        self.workflow_tasks[self._end_task_name(graph.name)] = workflow_end_task

    def execute(self):
        """
        Executes the workflow.
        """
        result = luigi.build(
            tasks=[self.workflow_task],
            workers=self.concurrency_count,
            # local_scheduler=True,
            logging_conf_file=self.engine_logger_conf,
        )
        self.failed = not result

    def assert_finished_successfully(self):
        assert self.failed is not None
        if self.failed:
            # todo: add AriaEngineError exception here
            raise Exception('Execution failed')

    def _get_tasks_from_dependencies(self, dependencies, default_dependencies=()):
        """
        Returns task list from a dependencies.
        """
        return [
            self.workflow_tasks[
                context.name
                if self._is_operation(context) else
                self._end_task_name(context.name)
            ]
            for context in dependencies
        ] or default_dependencies

    def _is_operation(self, task):
        return isinstance(task, OperationContext)

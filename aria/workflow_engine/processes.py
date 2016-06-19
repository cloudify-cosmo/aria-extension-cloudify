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

import os
from uuid import uuid4
from importlib import import_module
from multiprocessing import Process

from ..logger import LoggerMixin


class BaseProcess(LoggerMixin, Process):
    # todo: add documentation

    def __init__(
            self,
            handler_path,
            context,
            **kwargs):
        super(BaseProcess, self).__init__(**kwargs)
        self.id = str(uuid4())
        self.handler_path = handler_path
        self.context = context

        self.daemon = True

    def __repr__(self):
        return (
            '{cls.__name__}('
            'handler_path={self.handler_path}, '
            'context={self.context})'.format(cls=self.__class__, self=self))

    def run(self):
        self.logger.debug('start {self.handler_path} process'.format(self=self))
        self.set_environ()
        self._load_workflow_handler()
        self.run_handler()

    def set_environ(self):
        os.environ.update(self.context.execution_env)
        if self.context.plugin:
            pass  # todo: add plugin to path

    def _load_workflow_handler(self):
        module_name, spec_handler_name = self.handler_path.rsplit('.', 1)
        try:
            module = import_module(module_name)
            self.handler = getattr(module, spec_handler_name)
        except ImportError:
            # todo: exception handler
            raise
        except AttributeError:
            # todo: exception handler
            raise

    def run_handler(self):
        self.handler(context=self.context, **self.context.parameters)


class WorkflowProcess(BaseProcess):
    pass

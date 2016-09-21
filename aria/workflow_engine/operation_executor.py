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

from .processes import BaseProcess


def register_executor():
    return [
        OperationProcess,
        OperationStoryteller,
    ]


class OperationProcess(BaseProcess):
    pass


class OperationStoryteller(BaseProcess):
    def start(self):
        self.logger.info(
            '\n========================================\n'
            '\tRunning operation: {context.name}\n'
            '\tOperation description: {context.description}\n'
            '\tOperation id: {context.id}\n'
            '\tOperation details: {context!r}\n'
            '\tOperation parameters: {context.parameters}\n'
            '\tOperation engine options: {context.engine_options}\n'
            '\tworkflow context: {context.workflow_context}\n'
            '========================================'.format(context=self.context)
        )

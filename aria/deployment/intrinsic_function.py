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

from ..parser.framework.functions import Function, parse
from ..parser.scan import scan_properties


def plan_evaluation_handler(plan):
    return _handler('evaluate', plan=plan)


def _handler(evaluator, **evaluator_kwargs):
    def handler(v, scope, context, path):
        evaluated_value = v
        scanned = False
        while True:
            func = parse(evaluated_value,
                         scope=scope,
                         context=context,
                         path=path)
            if not isinstance(func, Function):
                break
            previous_evaluated_value = evaluated_value
            evaluated_value = getattr(func, evaluator)(**evaluator_kwargs)
            if scanned and previous_evaluated_value == evaluated_value:
                break
            scan_properties(
                evaluated_value,
                handler,
                scope=scope,
                context=context,
                path=path,
                replace=True)
            scanned = True
        return evaluated_value
    return handler

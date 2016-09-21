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

from uuid import uuid4
from functools import partial, wraps

from .workflow_engine.engine import Engine
from .exceptions import AriaError

# todo: mode to aria.__init__ ?


def workflow(
        func=None,
        workflow_context=True,
        simple_workflow=True,
        suffix_template=''):
    if func is None:
        return partial(
            workflow,
            workflow_context=workflow_context,
            simple_workflow=simple_workflow,
            suffix_template=suffix_template)

    @wraps(func)
    def wrapper(context, **custom_kwargs):
        run_engine = simple_workflow and workflow.main_workflow
        workflow.main_workflow = False

        workflow_name = _generate_workflow_name(
            func_name=func.__name__,
            suffix_template=suffix_template,
            context=context,
            **custom_kwargs)

        func_kwargs = _create_func_kwargs(
            custom_kwargs,
            context,
            add_context=workflow_context,
            workflow_name=workflow_name)

        _validate_func_arguments(func, func_kwargs)

        func(**func_kwargs)

        if run_engine:
            engine = Engine(context.concurrency_count)
            engine.create_workflow(context, func_kwargs['graph'])
            engine.execute()
            engine.assert_finished_successfully()

        return func_kwargs['graph']

    return wrapper
# multiprocess answer (won't work in multi-thread)
workflow.main_workflow = True


def operation(
        func=None,
        operation_context=True):
    if func is None:
        return partial(operation)

    @wraps(func)
    def wrapper(context, **custom_kwargs):
        func_kwargs = _create_func_kwargs(
            custom_kwargs,
            context,
            add_context=operation_context)
        _validate_func_arguments(func, func_kwargs)
        context.description = func.__doc__

        return func(**func_kwargs)
    return wrapper


def _generate_workflow_name(func_name, context, suffix_template, **custom_kwargs):
    return '{func_name}.{suffix}'.format(
        func_name=func_name,
        context=context,
        suffix=suffix_template.format(context=context, **custom_kwargs) or str(uuid4()))


def _create_func_kwargs(
        custom_kwargs,
        context,
        add_context=True,
        workflow_name=None):
    if add_context:
        custom_kwargs['context'] = context
    custom_kwargs.setdefault('graph', context.task_graph(workflow_name))
    return custom_kwargs


def _validate_func_arguments(func, func_kwargs):
    _KWARGS_FLAG = 8

    has_kwargs = func.func_code.co_flags & _KWARGS_FLAG != 0
    args_count = func.func_code.co_argcount

    # all args without the ones with default values
    args = func.func_code.co_varnames[:args_count]
    non_default_args = args[:len(func.func_defaults)] if func.func_defaults else args

    # Check if any args without default values is missing in the func_kwargs
    for arg in non_default_args:
        if arg not in func_kwargs:
            raise AriaError(
                "The argument '{arg}' doest not have a default value, and it "
                "isn't passed to {func.__name__}".format(arg=arg, func=func))

    # check if there are any extra kwargs
    extra_kwargs = [arg for arg in func_kwargs.keys() if arg not in args]

    # assert that the function has kwargs
    if extra_kwargs and not has_kwargs:
        raise AriaError("The following extra kwargs were supplied: {extra_kwargs}".format(
            extra_kwargs=extra_kwargs
        ))

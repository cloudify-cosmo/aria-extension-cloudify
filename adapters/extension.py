#
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved.
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

from functools import wraps
from contextlib import contextmanager

from aria import extension as aria_extension

from .context_adapter import CloudifyContextAdapter


@aria_extension.process_executor
class CloudifyExecutorExtension(object):

    def decorate(self):
        def decorator(function):
            @wraps(function)
            def wrapper(ctx, **operation_inputs):
                # We assume that any Cloudify-based plugin would use the plugins-common, thus two
                # different paths are created
                is_cloudify_dependent = ctx.task.plugin and any(
                    'cloudify_plugins_common' in w for w in ctx.task.plugin.wheels)

                if is_cloudify_dependent:
                    from cloudify import context
                    from cloudify.exceptions import (NonRecoverableError, RecoverableError)

                    with ctx.model.instrument(*ctx.INSTRUMENTATION_FIELDS):
                        # We need to create a new class dynamically, since CloudifyContextAdapter
                        # doesn't exist at runtime
                        ctx_adapter = type('_CloudifyContextAdapter',
                                           (CloudifyContextAdapter, context.CloudifyContext),
                                           {}, )(ctx)

                        exception = None
                        with _push_cfy_ctx(ctx_adapter, operation_inputs):
                            try:
                                function(ctx=ctx_adapter, **operation_inputs)
                            except NonRecoverableError as e:
                                ctx.task.abort(str(e))
                            except RecoverableError as e:
                                ctx.task.retry(str(e), retry_interval=e.retry_after)
                            except BaseException as e:
                                # Keep exception and raise it outside of "with", because
                                # contextmanager does not allow raising exceptions
                                exception = e
                        if exception is not None:
                            raise exception
                else:
                    function(ctx=ctx, **operation_inputs)
            return wrapper
        return decorator


@contextmanager
def _push_cfy_ctx(ctx, params):
    from cloudify import state

    try:
        # Support for Cloudify > 4.0
        with state.current_ctx.push(ctx, params) as current_ctx:
            yield current_ctx

    except AttributeError:
        # Support for Cloudify < 4.0
        try:
            original_ctx = state.current_ctx.get_ctx()
        except RuntimeError:
            original_ctx = None
        try:
            original_params = state.current_ctx.get_parameters()
        except RuntimeError:
            original_params = None

        state.current_ctx.set(ctx, params)
        try:
            yield state.current_ctx.get_ctx()
        finally:
            state.current_ctx.set(original_ctx, original_params)

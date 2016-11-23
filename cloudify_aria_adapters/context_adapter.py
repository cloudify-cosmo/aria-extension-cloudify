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

import functools
import os
import tempfile

from aria import extension
from aria.orchestrator.context import operation

DEPLOYMENT = 'deployment'
NODE_INSTANCE = 'node-instance'
RELATIONSHIP_INSTANCE = 'relationship-instance'


class CloudifyContext(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self.blueprint = _Blueprint(ctx)
        self.deployment = _Deployment(ctx)
        self.operation = _Operation(ctx)
        self.bootstrap_context = _Bootstrap(ctx)
        self.plugin = _Plugin(ctx)
        self.agent = _CloudifyAgent()
        self._node = None
        self._node_instance = None
        self._source = None
        self._target = None
        if isinstance(ctx, operation.NodeOperationContext):
            self._node = _Node(ctx, ctx.node)
            self._instance = _NodeInstance(ctx, node_instance=ctx.node_instance)
        elif isinstance(ctx, operation.RelationshipOperationContext):
            self._source = _RelationshipSubject(
                ctx,
                node=ctx.source_node,
                node_instance=ctx.source_node_instance)
            self._target = _RelationshipSubject(
                ctx,
                node=ctx.target_node,
                node_instance=ctx.target_node_instance)

    @property
    def type(self):
        if self._source:
            return RELATIONSHIP_INSTANCE
        elif self._instance:
            return NODE_INSTANCE
        else:
            return DEPLOYMENT

    @property
    def instance(self):
        self._verify_in_node_operation()
        return self._instance

    @property
    def node(self):
        self._verify_in_node_operation()
        return self._node

    @property
    def source(self):
        self._verify_in_relationship_operation()
        return self._source

    @property
    def target(self):
        self._verify_in_relationship_operation()
        return self._target

    @property
    def execution_id(self):
        return self._ctx.task.execution.id

    @property
    def workflow_id(self):
        return self._ctx.task.execution.workflow_name

    @property
    def rest_token(self):
        return None

    @property
    def task_id(self):
        return self._ctx.task.id

    @property
    def task_name(self):
        return self._ctx.task.operation_mapping

    @property
    def task_target(self):
        return None

    @property
    def task_queue(self):
        return None

    @property
    def logger(self):
        return self._ctx.logger

    def send_event(self, event):
        self.logger.info(event)

    @property
    def provider_context(self):
        return {}

    def get_resource(self, resource_path):
        return self._ctx.get_resource(resource_path)

    def get_resource_and_render(self, resource_path, template_variables=None):
        return self._ctx.get_resource_and_render(resource_path, variables=template_variables)

    def download_resource(self, resource_path, target_path=None):
        target_path = self._get_target_path(target_path, resource_path)
        self._ctx.download_resource(
            destination=target_path,
            path=resource_path)
        return target_path

    def download_resource_and_render(self,
                                     resource_path,
                                     target_path=None,
                                     template_variables=None):
        target_path = self._get_target_path(target_path, resource_path)
        self._ctx.download_resource_and_render(
            destination=target_path,
            path=resource_path,
            variables=template_variables)
        return target_path

    @staticmethod
    def _get_target_path(target_path, resource_path):
        if target_path:
            return target_path
        fd, target_path = tempfile.mkstemp(suffix=os.path.basename(resource_path))
        os.close(fd)
        return target_path

    def _verify_in_node_operation(self):
        if self.type != NODE_INSTANCE:
            self._ctx.task.abort(
                'ctx.node/ctx.instance can only be used in a {0} context but '
                'used in a {1} context.'.format(NODE_INSTANCE, self.type))

    def _verify_in_relationship_operation(self):
        if self.type != RELATIONSHIP_INSTANCE:
            self._ctx.task.abort(
                'ctx.source/ctx.target can only be used in a {0} context but '
                'used in a {1} context.'.format(RELATIONSHIP_INSTANCE,
                                                self.type))


class _Blueprint(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def id(self):
        return self._ctx.blueprint.id


class _Deployment(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def id(self):
        return self._ctx.deployment.id


class _Node(object):

    def __init__(self, ctx, node):
        self._ctx = ctx
        self._node = node

    @property
    def id(self):
        return self._node.id

    @property
    def name(self):
        return self._node.name

    @property
    def properties(self):
        return self._node.properties

    @property
    def type(self):
        return self._node.type

    @property
    def type_hierarchy(self):
        return self._node.type_hierarchy


class _NodeInstance(object):

    def __init__(self, ctx, node_instance):
        self._ctx = ctx
        self._node_instance = node_instance

    @property
    def id(self):
        return self._node_instance.id

    @property
    def runtime_properties(self):
        return self._node_instance.runtime_properties

    @runtime_properties.setter
    def runtime_properties(self, value):
        self._node_instance.runtime_properties = value

    def update(self, on_conflict=None):
        # TODO
        pass

    def refresh(self, force=False):
        # TODO
        pass

    @property
    def host_ip(self):
        return self._node_instance.ip

    @property
    def relationships(self):
        return [_Relationship(self._ctx, relationship_instance=relationship_instance) for
                relationship_instance in self._node_instance.outbound_relationship_instances]


class _Relationship(object):

    def __init__(self, ctx, relationship_instance):
        self._ctx = ctx
        self._relationship_instance = relationship_instance
        node_instance = relationship_instance.target_node_instance
        node = node_instance.node
        self.target = _RelationshipSubject(ctx, node=node, node_instance=node_instance)

    @property
    def type(self):
        return self._relationship_instance.relationship.type

    @property
    def type_hierarchy(self):
        return self._relationship_instance.relationship.type_hierarchy


class _RelationshipSubject(object):

    def __init__(self, ctx, node, node_instance):
        self._ctx = ctx
        self.node = _Node(ctx, node=node)
        self.instance = _NodeInstance(ctx, node_instance=node_instance)


class _Operation(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def name(self):
        return self._ctx.task.name

    @property
    def retry_number(self):
        return self._ctx.task.retry_count

    @property
    def max_retries(self):
        task = self._ctx.task
        if task.max_attempts == task.INFINITE_RETRIES:
            return task.INFINITE_RETRIES
        else:
            return task.max_attempts - 1

    def retry(self, message=None, retry_after=None):
        self._ctx.task.retry(message, retry_after)


class _Bootstrap(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self.cloudify_agent = _Stub()
        self.resources_prefix = ''

    def broker_config(self, *args, **kwargs):
        return {}


class _CloudifyAgent(object):

    def init_script(self, *args, **kwargs):
        return None


class _Plugin(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self._plugin = None

    @property
    def name(self):
        return self._ctx.task.plugin_name

    @property
    def package_name(self):
        return self._plugin_attr('package_name')

    @property
    def package_version(self):
        return self._plugin_attr('package_version')

    @property
    def prefix(self):
        # TODO
        return self._plugin_attr('prefix')

    @property
    def workdir(self):
        # TODO
        return self._plugin_attr('workdir')

    def _plugin_attr(self, attr):
        if not self._plugin:
            self._plugin = self._ctx.task.plugin
        if not self._plugin:
            return None
        return getattr(self._plugin, attr, None)


class _Stub(object):
    def __getattr__(self, item):
        return None


@extension.process_executor
class CloudifyExecutorExtension(object):

    def decorate(self):
        from cloudify import state
        from cloudify.exceptions import NonRecoverableError, RecoverableError

        def decorator(function):
            @functools.wraps(function)
            def wrapper(ctx, **operation_inputs):
                adapter = CloudifyContext(ctx)
                with state.current_ctx.push(adapter, operation_inputs):
                    try:
                        function(ctx=ctx, **operation_inputs)
                    except NonRecoverableError as e:
                        ctx.task.abort(str(e))
                    except RecoverableError as e:
                        ctx.task.retry(str(e), retry_interval=e.retry_after)
            return wrapper
        return decorator

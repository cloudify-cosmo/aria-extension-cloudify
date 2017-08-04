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

import os
import tempfile

from aria.orchestrator.context import operation


DEPLOYMENT = 'deployment'
NODE_INSTANCE = 'node-instance'
RELATIONSHIP_INSTANCE = 'relationship-instance'


class CloudifyContextAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self._blueprint = BlueprintAdapter(ctx)
        self._deployment = DeploymentAdapter(ctx)
        self._operation = OperationAdapter(ctx)
        self._bootstrap_context = BootstrapAdapter(ctx)
        self._plugin = PluginAdapter(ctx)
        self._agent = CloudifyAgentAdapter()
        self._node = None
        self._node_instance = None
        self._source = None
        self._target = None
        if isinstance(ctx, operation.NodeOperationContext):
            self._node = NodeAdapter(ctx, ctx.node_template, ctx.node)
            self._instance = NodeInstanceAdapter(ctx, ctx.node)
        elif isinstance(ctx, operation.RelationshipOperationContext):
            self._source = RelationshipTargetAdapter(
                ctx,
                ctx.source_node_template,
                ctx.source_node
            )
            self._target = RelationshipTargetAdapter(
                ctx,
                ctx.target_node_template,
                ctx.target_node
            )

    def __getattr__(self, item):
        try:
            return getattr(self._ctx, item)
        except AttributeError:
            return super(CloudifyContextAdapter, self).__getattribute__(item)

    @property
    def blueprint(self):
        return self._blueprint

    @property
    def deployment(self):
        return self._deployment

    @property
    def operation(self):
        return self._operation

    @property
    def bootstrap_context(self):
        return self._bootstrap_context

    @property
    def plugin(self):
        return self._plugin

    @property
    def agent(self):
        return self._agent

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
        return self._ctx.task.function

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
            path=resource_path
        )
        return target_path

    def download_resource_and_render(self,
                                     resource_path,
                                     target_path=None,
                                     template_variables=None):
        target_path = self._get_target_path(target_path, resource_path)
        self._ctx.download_resource_and_render(
            destination=target_path,
            path=resource_path,
            variables=template_variables
        )
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
                'used in a {1} context.'.format(NODE_INSTANCE, self.type)
            )

    def _verify_in_relationship_operation(self):
        if self.type != RELATIONSHIP_INSTANCE:
            self._ctx.task.abort(
                'ctx.source/ctx.target can only be used in a {0} context but '
                'used in a {1} context.'.format(RELATIONSHIP_INSTANCE,
                                                self.type)
            )


class BlueprintAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def id(self):
        return self._ctx.service_template.id


class DeploymentAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def id(self):
        return self._ctx.service.id


class NodeAdapter(object):

    def __init__(self, ctx, node_template, node):
        self._ctx = ctx
        self._node_template = node_template
        self._node = node

    @property
    def id(self):
        return self._node_template.id

    @property
    def name(self):
        return self._node_template.name

    @property
    def properties(self):
        return self._node.properties

    @property
    def type(self):
        return self._node_template.type.name

    @property
    def type_hierarchy(self):
        # We needed to modify the type hierarchy to be a list of strings that include the word
        # 'cloudify' in each one of them instead of 'aria', since in the Cloudify AWS plugin, that
        # we currently wish to support, if we want to attach an ElasticIP to a node, this node's
        # type_hierarchy property must be a list of strings only, and it must contain either the
        # string 'cloudify.aws.nodes.Instance', or the string 'cloudify.aws.nodes.Interface'.
        # In any other case, we won't be able to attach an ElasticIP to a node using the Cloudify
        # AWS plugin.
        type_hierarchy_names = [type_.name for type_ in self._node_template.type.hierarchy
                                if type_.name is not None]
        return [type_name.replace('aria', 'cloudify') for type_name in type_hierarchy_names]


class NodeInstanceAdapter(object):

    def __init__(self, ctx, node):
        self._ctx = ctx
        self._node = node

    @property
    def id(self):
        return self._node.id

    @property
    def runtime_properties(self):
        return self._node.attributes

    @runtime_properties.setter
    def runtime_properties(self, value):
        self._node.attributes = value

    def update(self, on_conflict=None):
        self._ctx.model.node.update(self._node)

    def refresh(self, force=False):
        self._ctx.model.node.refresh(self._node)

    @property
    def host_ip(self):
        return self._node.host_address

    @property
    def relationships(self):
        return [RelationshipAdapter(self._ctx, relationship=relationship) for
                relationship in self._node.outbound_relationships]


class RelationshipAdapter(object):

    def __init__(self, ctx, relationship):
        self._ctx = ctx
        self._relationship = relationship
        node = relationship.target_node
        node_template = node.node_template
        self.target = RelationshipTargetAdapter(ctx, node_template, node)

    @property
    def type(self):
        return self._relationship.type.name

    @property
    def type_hierarchy(self):
        return self._relationship.type.hierarchy


class RelationshipTargetAdapter(object):

    def __init__(self, ctx, node_template, node):
        self._ctx = ctx
        self.node = NodeAdapter(ctx, node_template=node_template, node=node)
        self.instance = NodeInstanceAdapter(ctx, node=node)


class OperationAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def name(self):
        # We needed to modify the operation's 'name' property in order to support the Cloudify AWS
        # plugin. It can't use ARIA's operation naming convention, as any operation we want to run
        # using the Cloudify AWS plugin must have its name in the format:
        # '<something>.<operation_name>'.
        aria_name = self._ctx.task.name
        return aria_name.split('@')[0].replace(':', '.')

    @property
    def retry_number(self):
        return self._ctx.task.attempts_count - 1

    @property
    def max_retries(self):
        task = self._ctx.task
        if task.max_attempts == task.INFINITE_RETRIES:
            return task.INFINITE_RETRIES
        else:
            return task.max_attempts - 1 if task.max_attempts > 0 else 0

    def retry(self, message=None, retry_after=None):
        self._ctx.task.retry(message, retry_after)


class BootstrapAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self.cloudify_agent = _Stub()
        self.resources_prefix = ''

    def broker_config(self, *args, **kwargs):
        return {}


class CloudifyAgentAdapter(object):

    def init_script(self, *args, **kwargs):
        return None


class PluginAdapter(object):

    def __init__(self, ctx):
        self._ctx = ctx
        self._plugin = None

    @property
    def name(self):
        return self._ctx.task.plugin.name

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
        return self._ctx.plugin_workdir

    def _plugin_attr(self, attr):
        if not self._plugin:
            self._plugin = self._ctx.task.plugin
        if not self._plugin:
            return None
        return getattr(self._plugin, attr, None)


class _Stub(object):
    def __getattr__(self, _):
        return None

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
import copy
import datetime
import contextlib

import pytest

from aria import (workflow, operation)
from aria.modeling import models
from aria.orchestrator import events
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.exceptions import ExecutorException
from aria.orchestrator.workflows.executor import process
from aria.orchestrator.workflows.core import (engine, graph_compiler)
from aria.orchestrator.exceptions import (TaskAbortException, TaskRetryException)
from aria.utils import type as type_

import tests
from tests import (mock, storage, conftest)
from tests.orchestrator.workflows.helpers import events_collector

from adapters import context_adapter


@pytest.fixture(autouse=True)
def cleanup_logger(request):
    conftest.logging_handler_cleanup(request)


class TestCloudifyContextAdapter(object):

    def test_node_instance_operation(self, executor, workflow_context):
        node_template = self._get_node_template(workflow_context)
        node_type = 'aria.plugin.nodes.App'
        node_instance_property = models.Property.wrap('hello', 'world')
        node_template.type = models.Type(variant='variant', name=node_type)
        node = self._get_node(workflow_context)
        node_instance_attribute = models.Attribute.wrap('hello2', 'world2')
        node.attributes[node_instance_attribute.name] = node_instance_attribute
        node.properties[node_instance_property.name] = node_instance_property
        workflow_context.model.node.update(node)
        workflow_context.model.node_template.update(node_template)

        out = self._run(executor, workflow_context, _test_node_instance_operation)

        node_template = self._get_node_template(workflow_context)
        node = self._get_node(workflow_context)
        assert out['type'] == context_adapter.NODE_INSTANCE
        assert out['node']['id'] == node_template.id
        assert out['node']['name'] == node_template.name
        assert out['node']['properties'] == \
               {node_instance_property.name: node_instance_property.value}
        assert out['node']['type'] == node_type
        assert out['node']['type_hierarchy'] == ['cloudify.plugin.nodes.App']
        assert out['instance']['id'] == node.id
        assert out['instance']['runtime_properties'] == \
               {node_instance_attribute.name: node_instance_attribute.value}
        assert not out['source']
        assert not out['target']

    def test_node_instance_relationships(self, executor, workflow_context):
        relationship_node_template = self._get_dependency_node_template(workflow_context)
        relationship_node_instance = self._get_dependency_node(workflow_context)
        relationship = relationship_node_instance.inbound_relationships[0]
        relationship_type = models.Type(variant='variant', name='test.relationships.Relationship')
        relationship.type = relationship_type
        workflow_context.model.relationship.update(relationship)

        out = self._run(executor, workflow_context, _test_node_instance_relationships)

        assert len(out['instance']['relationships']) == 1
        relationship = out['instance']['relationships'][0]
        assert relationship['type'] == relationship_type.name
        assert relationship['type_hierarchy'] == [relationship_type.name]
        assert relationship['target']['node']['id'] == relationship_node_template.id
        assert relationship['target']['instance']['id'] == relationship_node_instance.id

    def test_source_operation(self, executor, workflow_context):
        self._test_relationship_operation(executor, workflow_context, operation_end='source')

    def test_target_operation(self, executor, workflow_context):
        self._test_relationship_operation(executor, workflow_context, operation_end='target')

    def _test_relationship_operation(self, executor, workflow_context, operation_end):
        out = self._run(
            executor, workflow_context, _test_relationship_operation, operation_end=operation_end)

        source_node = self._get_node_template(workflow_context)
        source_node_instance = self._get_node(workflow_context)
        target_node = self._get_dependency_node_template(workflow_context)
        target_node_instance = self._get_dependency_node(workflow_context)
        assert out['type'] == context_adapter.RELATIONSHIP_INSTANCE
        assert out['source']['node']['id'] == source_node.id
        assert out['source']['instance']['id'] == source_node_instance.id
        assert out['target']['node']['id'] == target_node.id
        assert out['target']['instance']['id'] == target_node_instance.id
        assert not out['node']
        assert not out['instance']

    def test_host_ip(self, executor, workflow_context):
        node = self._get_node_template(workflow_context)
        node.type_hierarchy = ['aria.nodes.Compute']
        node_instance = self._get_node(workflow_context)
        node_instance.host_fk = node_instance.id
        node_instance_ip = '120.120.120.120'
        node_instance.attributes['ip'] = models.Attribute.wrap('ip', node_instance_ip)
        workflow_context.model.node_template.update(node)
        workflow_context.model.node.update(node_instance)

        out = self._run(executor, workflow_context, _test_host_ip)

        assert out['instance']['host_ip'] == node_instance_ip

    def test_get_and_download_resource_and_render(self, tmpdir, executor, workflow_context):
        resource_path = 'resource'
        variable = 'VALUE'
        content = '{{ctx.service.name}}-{{variable}}'
        rendered = '{0}-{1}'.format(workflow_context.service.name, variable)
        source = tmpdir.join(resource_path)
        source.write(content)
        workflow_context.resource.service.upload(
            entry_id=str(workflow_context.service.id),
            source=str(source),
            path=resource_path)

        out = self._run(executor, workflow_context, _test_get_and_download_resource_and_render,
                        inputs={'resource': resource_path,
                                'variable': variable})

        assert out['get_resource'] == content
        assert out['get_resource_and_render'] == rendered
        with open(out['download_resource'], 'rb') as f:
            assert f.read() == content
        with open(out['download_resource_and_render'], 'rb') as f:
            assert f.read() == rendered

        os.remove(out['download_resource'])
        os.remove(out['download_resource_and_render'])

    def test_retry(self, executor, workflow_context):
        message = 'retry-message'
        retry_interval = 0.01

        exception = self._run_and_get_task_exceptions(
            executor, workflow_context, _test_retry,
            inputs={'message': message, 'retry_interval': retry_interval},
            max_attempts=2
        )[-1]

        assert isinstance(exception, TaskRetryException)
        assert exception.message == message
        assert exception.retry_interval == retry_interval

        out = self._get_node(workflow_context).attributes['out'].value
        assert out['operation']['retry_number'] == 1
        assert out['operation']['max_retries'] == 1

    def test_logger_and_send_event(self, executor, workflow_context):
        # TODO: add assertions of output once process executor output can be captured
        message = 'logger-message'
        event = 'event-message'
        self._run(executor, workflow_context, _test_logger_and_send_event,
                  inputs={'message': message, 'event': event})

    def test_plugin(self, executor, workflow_context, tmpdir):
        plugin = self._put_plugin(workflow_context)
        out = self._run(executor, workflow_context, _test_plugin, plugin=plugin)

        expected_workdir = tmpdir.join(
            'workdir', 'plugins', str(workflow_context.service.id), plugin.name)
        assert out['plugin']['name'] == plugin.name
        assert out['plugin']['package_name'] == plugin.package_name
        assert out['plugin']['package_version'] == plugin.package_version
        assert out['plugin']['workdir'] == str(expected_workdir)

    def test_importable_ctx_and_inputs(self, executor, workflow_context):
        test_inputs = {'input1': 1, 'input2': 2}
        plugin = self._put_plugin(workflow_context, mock_cfy_plugin=True)

        out = self._run(executor, workflow_context, _test_importable_ctx_and_inputs,
                        inputs=test_inputs,
                        skip_common_assert=True,
                        plugin=plugin)
        assert out['inputs'] == test_inputs

    def test_non_recoverable_error(self, executor, workflow_context):
        message = 'NON_RECOVERABLE_MESSAGE'
        plugin = self._put_plugin(workflow_context, mock_cfy_plugin=True)

        exception = self._run_and_get_task_exceptions(
            executor, workflow_context, _test_non_recoverable_error,
            inputs={'message': message},
            skip_common_assert=True,
            plugin=plugin
        )[0]
        assert isinstance(exception, TaskAbortException)
        assert exception.message == message

    def test_recoverable_error(self, executor, workflow_context):
        message = 'RECOVERABLE_MESSAGE'
        plugin = self._put_plugin(workflow_context, mock_cfy_plugin=True)

        retry_interval = 0.01
        exception = self._run_and_get_task_exceptions(
            executor, workflow_context, _test_recoverable_error,
            inputs={'message': message, 'retry_interval': retry_interval},
            skip_common_assert=True,
            plugin=plugin
        )[0]
        assert isinstance(exception, TaskRetryException)
        assert message in exception.message
        assert exception.retry_interval == retry_interval

    def _test_common(self, out, workflow_context):
        assert out['execution_id'] == workflow_context.execution.id
        assert out['workflow_id'] == workflow_context.execution.workflow_name
        assert out['rest_token'] is None
        assert out['task_id'][0] == out['task_id'][1]
        assert out['task_name'][0] == out['task_name'][1]
        assert out['task_target'] is None
        assert out['task_queue'] is None
        assert out['provider_context'] == {}
        assert out['blueprint']['id'] == workflow_context.service_template.id
        assert out['deployment']['id'] == workflow_context.service.id
        assert out['operation']['name'][0] == out['operation']['name'][1]
        assert out['operation']['retry_number'][0] == out['operation']['retry_number'][1]
        assert out['operation']['max_retries'][0] == out['operation']['max_retries'][1] - 1
        assert out['bootstrap_context']['resources_prefix'] == ''
        assert out['bootstrap_context']['broker_config'] == {}
        assert out['bootstrap_context']['cloudify_agent']['any'] is None
        assert out['agent']['init_script'] is None

    def _run(self,
             executor,
             workflow_context,
             func,
             inputs=None,
             max_attempts=None,
             skip_common_assert=False,
             operation_end=None,
             plugin=None):
        interface_name = 'test'
        operation_name = 'op'
        op_dict = {'function': '{0}.{1}'.format(__name__, func.__name__),
                   'plugin': plugin,
                   'arguments': inputs or {}}
        node = self._get_node(workflow_context)

        if operation_end:
            actor = relationship = node.outbound_relationships[0]
            relationship.interfaces[interface_name] = mock.models.create_interface(
                relationship.source_node.service,
                interface_name,
                operation_name,
                operation_kwargs=op_dict
            )
            workflow_context.model.relationship.update(relationship)

        else:
            actor = node
            node.interfaces[interface_name] = mock.models.create_interface(
                node.service,
                interface_name,
                operation_name,
                operation_kwargs=op_dict
            )
            workflow_context.model.node.update(node)

        if inputs:
            operation_inputs = \
                actor.interfaces[interface_name].operations[operation_name].inputs
            for input_name, input in inputs.iteritems():
                operation_inputs[input_name] = models.Input(name=input_name,
                                                            type_name=type_.full_type_name(input))

        @workflow
        def mock_workflow(graph, **kwargs):
            task = api.task.OperationTask(
                actor,
                interface_name,
                operation_name,
                arguments=inputs or {},
                max_attempts=max_attempts
            )
            graph.add_tasks(task)

        tasks_graph = mock_workflow(ctx=workflow_context)
        graph_compiler.GraphCompiler(workflow_context, executor.__class__).compile(tasks_graph)
        eng = engine.Engine(executors={executor.__class__: executor})
        eng.execute(workflow_context)
        out = self._get_node(workflow_context).attributes['out'].value
        if not skip_common_assert:
            self._test_common(out, workflow_context)
        return out

    def _get_dependency_node_template(self, workflow_context):
        return workflow_context.model.node_template.get_by_name(
            mock.models.DEPENDENCY_NODE_TEMPLATE_NAME)

    def _get_dependency_node(self, workflow_context):
        return workflow_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    def _get_node_template(self, workflow_context):
        return workflow_context.model.node_template.get_by_name(
            mock.models.DEPENDENT_NODE_TEMPLATE_NAME)

    def _get_node(self, workflow_context):
        return workflow_context.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)

    def _run_and_get_task_exceptions(self, *args, **kwargs):
        signal = events.on_failure_task_signal
        with events_collector(signal) as collected:
            with pytest.raises(ExecutorException):
                self._run(*args, **kwargs)
        return [event['kwargs']['exception'] for event in collected[signal]]

    @pytest.fixture
    def executor(self):
        result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
        yield result
        result.close()

    @pytest.fixture
    def workflow_context(self, tmpdir):
        result = mock.context.simple(
            str(tmpdir),
            context_kwargs=dict(workdir=str(tmpdir.join('workdir')))
        )
        yield result
        storage.release_sqlite_storage(result.model)

    def _put_plugin(self, workflow_context, mock_cfy_plugin=False):
        name = 'PLUGIN'
        archive_name = 'ARCHIVE'
        package_name = 'PACKAGE'
        package_version = '0.1.1'

        plugin = models.Plugin(
            name=name,
            archive_name=archive_name,
            package_name=package_name,
            package_version=package_version,
            uploaded_at=datetime.datetime.now(),
            wheels=['cloudify_plugins_common'] if mock_cfy_plugin else []
        )

        workflow_context.model.plugin.put(plugin)

        return plugin


@operation
def _test_node_instance_operation(ctx):
    with _adapter(ctx) as (adapter, out):
        node = adapter.node
        instance = adapter.instance
        out.update({
            'node': {
                'id': node.id,
                'name': node.name,
                'properties': copy.deepcopy(node.properties),
                'type': node.type,
                'type_hierarchy': node.type_hierarchy
            },
            'instance': {
                'id': instance.id,
                'runtime_properties': copy.deepcopy(instance.runtime_properties)
            }
        })
        try:
            assert adapter.source
            out['source'] = True
        except TaskAbortException:
            out['source'] = False
        try:
            assert adapter.target
            out['target'] = True
        except TaskAbortException:
            out['target'] = False


@operation
def _test_node_instance_relationships(ctx):
    with _adapter(ctx) as (adapter, out):
        relationships = [{'type': r.type,
                          'type_hierarchy': [t.name for t in r.type_hierarchy],
                          'target': {'node': {'id': r.target.node.id},
                                     'instance': {'id': r.target.instance.id}}}
                         for r in adapter.instance.relationships]
        out['instance'] = {'relationships': relationships}


@operation
def _test_relationship_operation(ctx):
    with _adapter(ctx) as (adapter, out):
        out.update({
            'source': {'node': {'id': adapter.source.node.id},
                       'instance': {'id': adapter.source.instance.id}},
            'target': {'node': {'id': adapter.target.node.id},
                       'instance': {'id': adapter.target.instance.id}}
        })
        try:
            assert adapter.node
            out['node'] = True
        except TaskAbortException:
            out['node'] = False
        try:
            assert adapter.instance
            out['instance'] = True
        except TaskAbortException:
            out['instance'] = False


@operation
def _test_host_ip(ctx):
    with _adapter(ctx) as (adapter, out):
        out['instance'] = {'host_ip': adapter.instance.host_ip}


@operation
def _test_get_and_download_resource_and_render(ctx, resource, variable):
    with _adapter(ctx) as (adapter, out):
        out.update({
            'get_resource': adapter.get_resource(resource),
            'get_resource_and_render': adapter.get_resource_and_render(
                resource, template_variables={'variable': variable}
            ),
            'download_resource': adapter.download_resource(resource),
            'download_resource_and_render': adapter.download_resource_and_render(
                resource, template_variables={'variable': variable}
            )
        })


@operation
def _test_retry(ctx, message, retry_interval):
    with _adapter(ctx) as (adapter, out):
        op = adapter.operation
        out['operation'] = {'retry_number': op.retry_number, 'max_retries': op.max_retries}
        op.retry(message, retry_after=retry_interval)


@operation
def _test_logger_and_send_event(ctx, message, event):
    with _adapter(ctx) as (adapter, _):
        adapter.logger.info(message)
        adapter.send_event(event)


@operation
def _test_plugin(ctx):
    with _adapter(ctx) as (adapter, out):
        plugin = adapter.plugin
        out['plugin'] = {
            'name': plugin.name,
            'package_name': plugin.package_name,
            'package_version': plugin.package_version,
            'workdir': plugin.workdir
        }


@operation
def _test_importable_ctx_and_inputs(**_):
    from cloudify import ctx
    from cloudify.state import ctx_parameters
    ctx.instance.runtime_properties['out'] = {'inputs': dict(ctx_parameters)}


@operation
def _test_non_recoverable_error(message, **_):
    from cloudify.exceptions import NonRecoverableError
    raise NonRecoverableError(message)


@operation
def _test_recoverable_error(message, retry_interval, **_):
    from cloudify.exceptions import RecoverableError
    raise RecoverableError(message, retry_interval)


def _test_common(out, ctx, adapter):
    op = adapter.operation
    bootstrap_context = adapter.bootstrap_context
    out.update({
        'type': adapter.type,
        'execution_id': adapter.execution_id,
        'workflow_id': adapter.workflow_id,
        'rest_token': adapter.rest_token,
        'task_id': (adapter.task_id, ctx.task.id),
        'task_name': (adapter.task_name, ctx.task.function),
        'task_target': adapter.task_target,
        'task_queue': adapter.task_queue,
        'provider_context': adapter.provider_context,
        'blueprint': {'id': adapter.blueprint.id},
        'deployment': {'id': adapter.deployment.id},
        'operation': {
            'name': [op.name, ctx.name.split('@')[0].replace(':', '.')],
            'retry_number': [op.retry_number, ctx.task.attempts_count - 1],
            'max_retries': [op.max_retries, ctx.task.max_attempts]
        },
        'bootstrap_context': {
            'broker_config': bootstrap_context.broker_config('arg1', 'arg2', arg3='arg3'),
            # All attribute access of cloudify_agent returns none
            'cloudify_agent': {'any': bootstrap_context.cloudify_agent.any},
            'resources_prefix': bootstrap_context.resources_prefix
        },
        'agent': {
            'init_script': adapter.agent.init_script('arg1', 'arg2', arg3='arg3')
        }
    })


@contextlib.contextmanager
def _adapter(ctx):
    out = {}
    adapter = context_adapter.CloudifyContextAdapter(ctx)
    _test_common(out, ctx, adapter)
    try:
        yield adapter, out
    finally:
        try:
            instance = adapter.instance
        except TaskAbortException:
            instance = adapter.source.instance
        instance.runtime_properties['out'] = out

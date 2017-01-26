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

import copy
import contextlib
import datetime
import os

import pytest

from aria import workflow, operation
from aria.orchestrator import events
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.exceptions import ExecutorException
from aria.orchestrator.workflows.executor import process
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.exceptions import TaskAbortException, TaskRetryException

import tests
from tests import mock, storage
from tests.orchestrator.workflows.helpers import events_collector

from cloudify_aria_adapters import context_adapter


class TestCloudifyContextAdapter(object):

    def test_node_instance_operation(self, executor, workflow_context):
        node = self._get_node(workflow_context)
        node_properties = {'hello': 'world'}
        node_type = 'test.nodes.App'
        node_type_hierarchy = [node_type]
        node.properties = node_properties
        node.type = node_type
        node.type_hierarchy = node_type_hierarchy
        node_instance = self._get_node_instance(workflow_context)
        node_instance_runtime_properties = {'hello2': 'world2'}
        node_instance.runtime_properties = node_instance_runtime_properties
        workflow_context.model.node_instance.update(node_instance)
        workflow_context.model.node.update(node)

        out = self._run(executor, workflow_context, _test_node_instance_operation)

        node = self._get_node(workflow_context)
        node_instance = self._get_node_instance(workflow_context)
        assert out['type'] == context_adapter.NODE_INSTANCE
        assert out['node']['id'] == node.id
        assert out['node']['name'] == node.name
        assert out['node']['properties'] == node_properties
        assert out['node']['type'] == node_type
        assert out['node']['type_hierarchy'] == node_type_hierarchy
        assert out['instance']['id'] == node_instance.id
        assert out['instance']['runtime_properties'] == node_instance_runtime_properties
        assert not out['source']
        assert not out['target']

    def test_node_instance_relationships(self, executor, workflow_context):
        relationship_node = self._get_dependency_node(workflow_context)
        relationship = relationship_node.inbound_relationships[0]
        relationship_node_instance = self._get_dependency_node_instance(workflow_context)
        relationship_type = 'test.relationships.Relationship'
        relationship_type_hierarchy = [relationship_type]
        relationship.type = relationship_type
        relationship.type_hierarchy = relationship_type_hierarchy
        workflow_context.model.relationship.update(relationship)

        out = self._run(executor, workflow_context, _test_node_instance_relationships)

        assert len(out['instance']['relationships']) == 1
        relationship = out['instance']['relationships'][0]
        assert relationship['type'] == relationship_type
        assert relationship['type_hierarchy'] == relationship_type_hierarchy
        assert relationship['target']['node']['id'] == relationship_node.id
        assert relationship['target']['instance']['id'] == relationship_node_instance.id

    def test_source_operation(self, executor, workflow_context):
        self._test_relationship_operation(executor, workflow_context,
                                          operation_end=api.task.OperationTask.SOURCE_OPERATION)

    def test_target_operation(self, executor, workflow_context):
        self._test_relationship_operation(executor, workflow_context,
                                          operation_end=api.task.OperationTask.TARGET_OPERATION)

    def _test_relationship_operation(self, executor, workflow_context, operation_end):
        out = self._run(executor, workflow_context, _test_relationship_operation,
                        operation_end=operation_end)

        source_node = self._get_node(workflow_context)
        source_node_instance = self._get_node_instance(workflow_context)
        target_node = self._get_dependency_node(workflow_context)
        target_node_instance = self._get_dependency_node_instance(workflow_context)
        assert out['type'] == context_adapter.RELATIONSHIP_INSTANCE
        assert out['source']['node']['id'] == source_node.id
        assert out['source']['instance']['id'] == source_node_instance.id
        assert out['target']['node']['id'] == target_node.id
        assert out['target']['instance']['id'] == target_node_instance.id
        assert not out['node']
        assert not out['instance']

    def test_host_ip(self, executor, workflow_context):
        node = self._get_node(workflow_context)
        node.type_hierarchy = ['aria.nodes.Compute']
        node_instance = self._get_node_instance(workflow_context)
        node_instance.host_fk = node_instance.id
        node_instance_ip = '120.120.120.120'
        node_instance.runtime_properties = {'ip': node_instance_ip}
        workflow_context.model.node.update(node)
        workflow_context.model.node_instance.update(node_instance)

        out = self._run(executor, workflow_context, _test_host_ip)

        assert out['instance']['host_ip'] == node_instance_ip

    def test_get_and_download_resource_and_render(self, tmpdir, executor, workflow_context):
        resource_path = 'resource'
        variable = 'VALUE'
        content = '{{ctx.deployment.name}}-{{variable}}'
        rendered = '{0}-{1}'.format(workflow_context.deployment.name, variable)
        source = tmpdir.join(resource_path)
        source.write(content)
        workflow_context.resource.deployment.upload(
            entry_id=str(workflow_context.deployment.id),
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
            max_attempts=2)[-1]

        assert isinstance(exception, TaskRetryException)
        assert exception.message == message
        assert exception.retry_interval == retry_interval

        out = self._get_node_instance(workflow_context).runtime_properties['out']
        assert out['operation']['retry_number'] == 1
        assert out['operation']['max_retries'] == 1

    def test_logger_and_send_event(self, executor, workflow_context):
        # TODO: add assertions of output once process executor output can be captured
        message = 'logger-message'
        event = 'event-message'
        self._run(executor, workflow_context, _test_logger_and_send_event,
                  inputs={'message': message, 'event': event})

    def test_plugin(self, executor, workflow_context, tmpdir):
        name = 'PLUGIN'
        package_name = 'PACKAGE'
        package_version = '0.1.1'
        plugin = workflow_context.model.plugin.model_cls(
            archive_name='',
            package_name=package_name,
            package_version=package_version,
            uploaded_at=datetime.datetime.now(),
            wheels=[],
        )
        workflow_context.model.plugin.put(plugin)
        node = self._get_node(workflow_context)
        node.plugins = [{'name': name,
                         'package_name': package_name,
                         'package_version': package_version}]
        workflow_context.model.node.update(node)

        out = self._run(executor, workflow_context, _test_plugin, plugin=name)

        expected_workdir = tmpdir.join('workdir', 'plugins', str(workflow_context.deployment.id),
                                       name)
        assert out['plugin']['name'] == name
        assert out['plugin']['package_name'] == package_name
        assert out['plugin']['package_version'] == package_version
        assert out['plugin']['workdir'] == str(expected_workdir)

    def test_importable_ctx_and_inputs(self, executor, workflow_context):
        test_inputs = {'input1': 1, 'input2': 2}
        out = self._run(executor, workflow_context, _test_importable_ctx_and_inputs,
                        inputs=test_inputs,
                        skip_common_assert=True)
        assert out['inputs'] == test_inputs

    def test_non_recoverable_error(self, executor, workflow_context):
        message = 'NON_RECOVERABLE_MESSAGE'
        exception = self._run_and_get_task_exceptions(
            executor, workflow_context, _test_non_recoverable_error,
            inputs={'message': message},
            skip_common_assert=True)[0]
        assert isinstance(exception, TaskAbortException)
        assert exception.message == message

    def test_recoverable_error(self, executor, workflow_context):
        message = 'RECOVERABLE_MESSAGE'
        retry_interval = 0.01
        exception = self._run_and_get_task_exceptions(
            executor, workflow_context, _test_recoverable_error,
            inputs={'message': message, 'retry_interval': retry_interval},
            skip_common_assert=True)[0]
        assert isinstance(exception, TaskRetryException)
        assert message in exception.message
        assert exception.retry_interval == retry_interval

    def test_node_instance_update_and_refresh(self, executor, workflow_context):
        expected_initial = self._get_node_instance(workflow_context).runtime_properties
        updated = {'new': 'runtime', 'property': 'value'}
        uncommitted_change = {'newer': 'runtime', 'properties': 'and values'}
        inputs = {'updated': updated, 'uncommitted_change': uncommitted_change}
        out = self._run(executor, workflow_context, _test_node_instance_update_and_refresh,
                        inputs=inputs)
        props = out['instance']['runtime_properties']
        expected_updated = expected_initial.copy()
        expected_updated.update(updated)
        expected_uncommitted_change = expected_updated.copy()
        expected_uncommitted_change.update(uncommitted_change)
        expected_refreshed = expected_updated
        assert props['initial'] == expected_initial
        assert props['after_update'] == expected_updated
        assert props['after_change'] == expected_uncommitted_change
        assert props['after_refresh'] == expected_refreshed

    @pytest.mark.skip('Pending ARIA feature implementation')
    def test_plugin_prefix(self):
        assert False

    def _test_common(self, out, workflow_context):
        assert out['execution_id'] == workflow_context.execution.id
        assert out['workflow_id'] == workflow_context.execution.workflow_name
        assert out['rest_token'] is None
        assert out['task_id'][0] == out['task_id'][1]
        assert out['task_name'][0] == out['task_name'][1]
        assert out['task_target'] is None
        assert out['task_queue'] is None
        assert out['provider_context'] == {}
        assert out['blueprint']['id'] == workflow_context.blueprint.id
        assert out['deployment']['id'] == workflow_context.deployment.id
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
             operation_end=None,
             inputs=None,
             max_attempts=None,
             plugin=None,
             skip_common_assert=False):
        @workflow
        def mock_workflow(ctx, graph):
            op = 'test.op'
            op_dict = {'operation': '{0}.{1}'.format(__name__, func.__name__), 'plugin': plugin}
            node_instance = self._get_node_instance(ctx)
            if operation_end:
                relationship_instance = node_instance.outbound_relationship_instances[0]
                relationship = relationship_instance.relationship
                getattr(relationship, operation_end)[op] = op_dict
                task = api.task.OperationTask.relationship_instance(
                    instance=relationship_instance,
                    name=op,
                    operation_end=operation_end,
                    inputs=inputs or {},
                    max_attempts=max_attempts)
            else:
                node_instance.node.operations[op] = op_dict
                task = api.task.OperationTask.node_instance(
                    instance=node_instance,
                    name=op,
                    inputs=inputs or {},
                    max_attempts=max_attempts)
            graph.add_tasks(task)
        tasks_graph = mock_workflow(ctx=workflow_context)
        eng = engine.Engine(
            executor=executor,
            workflow_context=workflow_context,
            tasks_graph=tasks_graph)
        eng.execute()
        out = self._get_node_instance(workflow_context).runtime_properties['out']
        if not skip_common_assert:
            self._test_common(out, workflow_context)
        return out

    def _get_dependency_node(self, workflow_context):
        return workflow_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    def _get_dependency_node_instance(self, workflow_context):
        return workflow_context.model.node_instance.get_by_name(
            mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

    def _get_node(self, workflow_context):
        return workflow_context.model.node.get_by_name(mock.models.DEPENDENT_NODE_NAME)

    def _get_node_instance(self, workflow_context):
        return workflow_context.model.node_instance.get_by_name(
            mock.models.DEPENDENT_NODE_INSTANCE_NAME)

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
        result = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)),
                                     resources_dir=str(tmpdir.join('resources')),
                                     workdir=str(tmpdir.join('workdir')))
        yield result
        storage.release_sqlite_storage(result.model)


@operation
def _test_node_instance_operation(ctx):
    with _adapter(ctx) as (adapter, out):
        node = adapter.node
        instance = adapter.instance
        out.update({
            'node': {
                'id': node.id,
                'name': node.name,
                'properties': node.properties,
                'type': node.type,
                'type_hierarchy': node.type_hierarchy
            },
            'instance': {
                'id': instance.id,
                'runtime_properties': copy.deepcopy(instance.runtime_properties),
            },
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
                          'type_hierarchy': r.type_hierarchy,
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
                resource, template_variables={'variable': variable}),
            'download_resource': adapter.download_resource(resource),
            'download_resource_and_render': adapter.download_resource_and_render(
                resource, template_variables={'variable': variable}
            ),
        })


@operation
def _test_retry(ctx, message, retry_interval):
    with _adapter(ctx) as (adapter, out):
        op = adapter.operation
        out['operation'] = {'retry_number': op.retry_number, 'max_retries': op.max_retries}
        op.retry(message, retry_after=retry_interval)


@operation
def _test_logger_and_send_event(ctx, message, event):
    with _adapter(ctx) as (adapter, out):
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
def _test_node_instance_update_and_refresh(ctx, updated, uncommitted_change):
    with _adapter(ctx) as (adapter, out):
        runtime_properties = {'initial': copy.deepcopy(adapter.instance.runtime_properties)}
        out['instance'] = {'runtime_properties': runtime_properties}
        adapter.instance.runtime_properties.update(updated)
        adapter.instance.update()
        runtime_properties['after_update'] = copy.deepcopy(adapter.instance.runtime_properties)
        adapter.instance.runtime_properties.update(uncommitted_change)
        runtime_properties['after_change'] = copy.deepcopy(adapter.instance.runtime_properties)
        adapter.instance.refresh()
        runtime_properties['after_refresh'] = copy.deepcopy(adapter.instance.runtime_properties)


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
        'task_name': (adapter.task_name, ctx.task.operation_mapping),
        'task_target': adapter.task_target,
        'task_queue': adapter.task_queue,
        'provider_context': adapter.provider_context,
        'blueprint': {'id': adapter.blueprint.id},
        'deployment': {'id': adapter.deployment.id},
        'operation': {
            'name': (op.name, ctx.task.name),
            'retry_number': (op.retry_number, ctx.task.retry_count),
            'max_retries': (op.max_retries, ctx.task.max_attempts)
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
    adapter = context_adapter.CloudifyContext(ctx)
    _test_common(out, ctx, adapter)
    try:
        yield adapter, out
    finally:
        try:
            instance = adapter.instance
        except TaskAbortException:
            instance = adapter.source.instance
        instance.runtime_properties['out'] = out

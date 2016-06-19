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
import json
import os
import sys
from glob import glob
from importlib import import_module
from itertools import chain
from pprint import pprint
from uuid import uuid4

from yaml import safe_load, YAMLError

from aria.deployment import prepare_deployment_plan
from aria.logger import LoggerMixin
from aria.process import Process

# from aria.parser import Parser
from aria.parser.framework.functions import evaluate_outputs
from aria.parser.utils import create_import_resolver
from aria.parser.constants import (
    PLUGIN_INSTALL_KEY,
    PLUGIN_SOURCE_KEY,
    DEPLOYMENT_PLUGINS_TO_INSTALL,
    NODES,
    PLUGINS,
)
from aria.storage import FileSystemModelDriver, FileSystemResourceDriver, ResourceStorage
from aria import application_model_storage, application_resource_storage
from aria.appilcation_tools import StorageManager
from aria.contexts import WorkflowContext
from aria.workflow_engine.processes import WorkflowProcess

from .storage import (
    local_resource_storage,
    create_local_storage,
    local_model_storage,
    create_user_space,
    user_space,
    local_storage,
)
from . import config

#######################################
from dsl_parser.parser import parse_from_path
from dsl_parser.tasks import prepare_deployment_plan
#######################################


class AriaCliError(Exception):
    pass


class AriaCliFormatInputsError(AriaCliError):
    def __init__(self, message, inputs):
        self.inputs = inputs
        super(AriaCliFormatInputsError, self).__init__(message)

    def user_message(self):
        return (
            'Invalid input format: {0}, '
            'the expected format is: '
            'key1=value1;key2=value2'.format(self.inputs))


class AriaCliYAMLInputsError(AriaCliError):
    pass


class AriaCliInvalidInputsError(AriaCliFormatInputsError):
    def user_message(self):
        return (
            'Invalid input: {0}. input must represent a dictionary.\n'
            'Valid values can be one of:\n'
            '- a path to a YAML file\n'
            '- a path to a directory containing YAML files\n'
            '- a single quoted wildcard based path (e.g. "*-inputs.yaml")\n'
            '- a string formatted as JSON\n'
            '- a string formatted as key1=value1;key2=value2'.format(self.inputs)
        )


class BaseCommand(LoggerMixin):
    def __repr__(self):
        return 'AriaCli({cls.__name__})'.format(cls=self.__class__)

    def __call__(self, args_namespace):
        """
        __call__ method is called when running command
        :param args_namespace:
        """
        pass

    def parse_inputs(self, inputs):
        """
        Returns a dictionary of inputs `resources` can be:
        - A list of files.
        - A single file
        - A directory containing multiple input files
        - A key1=value1;key2=value2 pairs string.
        - Wildcard based string (e.g. *-inputs.yaml)
        """

        parsed_dict = {}

        def format_to_dict(input_string):
            self.logger.info('Processing inputs source: {0}'.format(input_string))
            try:
                input_string = input_string.strip()
                try:
                    parsed_dict.update(json.loads(input_string))
                except:
                    parsed_dict.update((input.split('=')
                                       for input in input_string.split(';')
                                       if input))
            except Exception as exc:
                raise AriaCliFormatInputsError(str(exc), inputs=input_string)

        def handle_inputs_source(input_path):
            self.logger.info('Processing inputs source: {0}'.format(input_path))
            try:
                with open(input_path) as input_file:
                    content = safe_load(input_file)
            except YAMLError as exc:
                raise AriaCliYAMLInputsError(
                    '"{0}" is not a valid YAML. {1}'.format(input_path, str(exc)))
            if isinstance(content, dict):
                parsed_dict.update(content)
                return
            if content is None:
                return
            raise AriaCliInvalidInputsError('Invalid inputs', inputs=input_path)

        for input_string in inputs if isinstance(inputs, list) else [inputs]:
            if os.path.isdir(input_string):
                for input_file in os.listdir(input_string):
                    handle_inputs_source(os.path.join(input_string, input_file))
                continue
            input_files = glob(input_string)
            if input_files:
                for input_file in input_files:
                    handle_inputs_source(input_file)
                continue
            format_to_dict(input_string)
        return parsed_dict


class InitCommand(BaseCommand):
    _IN_VIRTUAL_ENV = hasattr(sys, 'real_prefix')

    def __call__(self, args_namespace):
        super(InitCommand, self).__call__(args_namespace)
        self.workspace_setup()
        inputs = self.parse_inputs(args_namespace.input) if args_namespace.input else None
        plan, deployment_plan = self.parse_blueprint(args_namespace.blueprint_path, inputs)
        if args_namespace.install_plugins:
            self.install_plugins(path=args_namespace.blueprint_path, plan=plan)
        self.validate_plugins(deployment_plan)

        self.create_storage(
            blueprint_plan=plan,
            blueprint_path=args_namespace.blueprint_path,
            deployment_plan=deployment_plan,
            blueprint_id=args_namespace.blueprint_id,
            deployment_id=args_namespace.deployment_id,
            main_file_name=os.path.basename(args_namespace.blueprint_path))
        self.logger.info('Initiated {0}'.format(args_namespace.blueprint_path))
        self.logger.info(
            'If you make changes to the blueprint, '
            'run `cfy local init` command again to apply them'.format(
                args_namespace.blueprint_path))

    def workspace_setup(self):
        try:
            create_user_space()
            self.logger.debug(
                'created user space path in: {0}'.format(user_space()))
        except IOError:
            self.logger.debug(
                'user space path already exist - {0}'.format(user_space()))
        try:
            create_local_storage()
            self.logger.debug(
                'created local storage path in: {0}'.format(local_storage()))
        except IOError:
            self.logger.debug(
                'local storage path already exist - {0}'.format(local_storage()))
        return local_storage()

    def parse_blueprint(self, blueprint_path, inputs=None):
        # resolver = create_import_resolver(config.import_resolver)
        # self.logger.debug('created parser resolver: {0!r}'.format(resolver))

        # plan = Parser(import_resolver=resolver).parse(blueprint_path)
        # todo: remove after debug
        plan = parse_from_path(blueprint_path)

        self.logger.info('blueprint parsed successfully')
        deployment_plan = prepare_deployment_plan(plan=plan.copy(), inputs=inputs)
        # todo: application level api? maybe:
        # todo: deployment_plan/blueprint = aria.application.parse_blueprint(blueprint_path, inputs=None))
        return plan, deployment_plan

    def install_plugins(self, path, plan):
        requirements = self.find_all_requirements(path, plan)
        if not requirements:
            self.logger.debug('There are no plugins to install')
            return
        if not self._IN_VIRTUAL_ENV:
            self.logger.warnint(
                'install blueprint plugins not in virtual env '
                'can cause an issues in your env')
        command_line = chain(
            (sys.executable, '-m', 'pip', 'install'),
            requirements)
        process = Process(args=command_line)
        process.run()
        process.raise_failure()
        self.logger.info('requirements install successfully')

    def create_storage(
            self,
            blueprint_path,
            blueprint_plan,
            deployment_plan,
            blueprint_id,
            deployment_id,
            main_file_name=None):
        resource_storage = application_resource_storage(
            FileSystemResourceDriver(local_resource_storage()))
        model_storage = application_model_storage(
            FileSystemModelDriver(local_model_storage()))
        resource_storage.setup()
        model_storage.setup()

        storage_manager = StorageManager(
            model_storage=model_storage,
            resource_storage=resource_storage,
            blueprint_path=blueprint_path,
            blueprint_id=blueprint_id,
            blueprint_plan=blueprint_plan,
            deployment_id=deployment_id,
            deployment_plan=deployment_plan
        )

        storage_manager.create_blueprint_storage(
            blueprint_path,
            main_file_name=main_file_name)
        storage_manager.create_nodes_storage()

        storage_manager.create_deployment_storage()
        storage_manager.create_node_instances_storage()

        # todo: create resources/
        # todo: I'm here...
        # todo: maybe move to Aria SDK level...
        # todo: create application level SDK...

    def validate_plugin_exists(
            self,
            plugin_name,
            module_method_path,
            node_name='',
            ignored_modules=()):
        module_name = '.'.join(module_method_path.split('.')[:-1])
        method_name = module_method_path.split('.')[-1]
        if module_name in ignored_modules:
            return
        try:
            plugin = import_module(module_name)
        except ImportError:
            # todo: sort exceptions
            raise ImportError(
                'mapping error: No module named {0} [node={1}, type={2}]'.format(
                    module_name, node_name, plugin_name))
        try:
            getattr(plugin, method_name)
        except AttributeError:
            # todo: sort exceptions
            raise AttributeError(
                'mapping error: {0} has no attribute "{1}" [node={2}, type={3}]'.format(
                    plugin.__name__, method_name, node_name, plugin_name))

    def validate_plugins(self, plan):
        def iter_operations(operations):
            for operation in operations.itervalues():
                operation = operation.get('operation')
                if not operation:
                    continue
                yield operation

        for node in plan['nodes']:
            for operation in iter_operations(node.get('operations', {})):
                self.validate_plugin_exists(
                    plugin_name='operations',
                    module_method_path=operation,
                    node_name=node['id'])

            for relationship in node['relationships']:
                source_operations = relationship.get('source_operations', {})
                for operation in iter_operations(source_operations):
                    self.validate_plugin_exists(
                        plugin_name='source_operations',
                        module_method_path=operation,
                        node_name=node['id'])
                target_operations = relationship.get('target_operations', {})
                for operation in iter_operations(target_operations):
                    self.validate_plugin_exists(
                        plugin_name='target_operations',
                        module_method_path=operation,
                        node_name=node['id'])

    def find_all_requirements(self, path, plan):
        directory = os.path.abspath(os.path.dirname(path))
        requirements = set()

        def plugins_to_requirements(plugins):
            for plugin in plugins:
                if not plugin[PLUGIN_INSTALL_KEY]:
                    continue
                source = plugin[PLUGIN_SOURCE_KEY]
                if not source:
                    continue
                if '://' in source:
                    plugin_path = source
                else:
                    # Local plugin (should reside under the 'plugins' dir)
                    plugin_path = os.path.join(directory, 'plugins', source)
                self.logger.debug('found plugin: {0}'.format(plugin_path))
                requirements.add(plugin_path)

        plugins_to_requirements(plan[DEPLOYMENT_PLUGINS_TO_INSTALL])
        for node in plan[NODES]:
            plugins_to_requirements(node[PLUGINS])

        return requirements


class RequirementsCommand(InitCommand):
    def __call__(self, args_namespace):
        super(RequirementsCommand, self).__call__(args_namespace)
        plan, _ = self.parse_blueprint(args_namespace.blueprint_path)
        requirements = self.find_all_requirements(args_namespace.blueprint_path, plan)
        if not requirements:
            self.logger.info('found no requirements')
            return

        self.logger.info('found requirements:')
        for index, requirement in enumerate(requirements, 1):
            self.logger.info('\t{index}: {requirement}'.format(
                index=index, requirement=requirement))

        if not args_namespace.output:
            return
        if os.path.exists(args_namespace.output):
            self.logger.error('Output path {0} already exists'.format(args_namespace.output))
            return
        with open(args_namespace.output, 'w') as output:
            output.writelines(requirements)


class ExecuteCommand(BaseCommand):
    def __call__(self, args_namespace):
        super(ExecuteCommand, self).__call__(args_namespace)
        parameters = self.parse_inputs(args_namespace.parameters) if args_namespace.parameters else {}
        storage = application_model_storage(FileSystemModelDriver(local_model_storage()))
        deployment = storage.deployment.get(args_namespace.deployment_id)

        try:
            workflow = deployment.workflows[args_namespace.workflow_id]
        except KeyError:
            # todo: sort exception...
            raise ValueError(
                '{0} workflow does not exist. existing workflows are: {1}'.format(
                    args_namespace.workflow_id,
                    deployment.workflows.keys()))

        workflow_parameters = self._merge_and_validate_execution_parameters(
            workflow,
            args_namespace.workflow_id,
            parameters)

        workflow_context = WorkflowContext(
            name=args_namespace.workflow_id,
            model_storage=storage,
            resource_storage='',
            deployment_id=args_namespace.deployment_id,
            workflow_id=args_namespace.workflow_id,
            parameters=workflow_parameters,
            concurrency_count=args_namespace.task_thread_pool_size,
        )
        workflow_process = WorkflowProcess(
            handler_path=workflow['operation'],
            context=workflow_context)
        workflow_process.start()
        workflow_process.join()
        assert workflow_process.exitcode == 0, ':-('

    def _merge_and_validate_execution_parameters(
            self,
            workflow,
            workflow_name,
            execution_parameters):
        merged_parameters = {}
        workflow_parameters = workflow.get('parameters', {})
        missing_mandatory_parameters = set()

        for name, param in workflow_parameters.iteritems():
            if 'default' not in param:
                if name not in execution_parameters:
                    missing_mandatory_parameters.add(name)
                    continue
                merged_parameters[name] = execution_parameters[name]
                continue
            merged_parameters[name] = execution_parameters[name] if name in execution_parameters else param['default']

        if missing_mandatory_parameters:
            raise ValueError(
                'Workflow "{0}" must be provided with the following '
                'parameters to execute: {1}'.format(
                    workflow_name, ','.join(missing_mandatory_parameters)))

        custom_parameters = dict(
            (k, v) for (k, v) in execution_parameters.iteritems()
            if k not in workflow_parameters)

        if custom_parameters:
            raise ValueError(
                'Workflow "{0}" does not have the following parameters declared: {1}. '
                'Remove these parameters'.format(
                    workflow_name, ','.join(custom_parameters.keys())))

        return merged_parameters


class InstallCommand(InitCommand, ExecuteCommand):
    def __call__(self, args_namespace):
        super(InstallCommand, self).__call__(args_namespace)
        # todo: execute


class UninstallCommand(ExecuteCommand):  # ?
    def __call__(self, args_namespace):
        super(ExecuteCommand, self).__call__(args_namespace)
        # todo: cleanup storage
        pass


class InstancesCommand(BaseCommand):
    def __call__(self, args_namespace):
        super(InstancesCommand, self).__call__(args_namespace)
        directory = local_model_storage(args_namespace.deployment_id)
        storage_driver = FileSystemResourceDriver(directory)
        storage = ResourceStorage(storage_driver)
        filters = {'node_id': args_namespace.node_id} if args_namespace.node_id else {}
        for node_instance in storage.iter_from_node_instance(filters=filters):
            self.logger.info('found node-instance for id: {0}'.format(node_instance['node_id']))
            self.logger.debug('node-instance info: {0}'.format(node_instance))
            # todo: need better display format
            pprint(node_instance)


class PluginsCommand(InitCommand):
    def __call__(self, args_namespace):
        plan, deployment_plan = self.parse_blueprint(args_namespace.blueprint_path)
        self.install_plugins(path=args_namespace.blueprint_path, plan=plan)
        self.validate_plugins(deployment_plan)


class OutputCommand(BaseCommand):
    def __call__(self, args_namespace):
        storage = self.model_storage(args_namespace.deployment_id)
        deployment_plan = storage.get_from_deployment(target=args_namespace.deployment_id)

        def get_node_instances_method():
            return list(storage.iter_from_node_instance())

        return evaluate_outputs(
            outputs_def=deployment_plan['outputs'],
            get_node_instances_method=get_node_instances_method,
            get_node_instance_method=storage.get_from_node_instance,
            get_node_method=storage.get_from_node)

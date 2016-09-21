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

import argparse
from functools import partial
from multiprocessing import cpu_count

# todo: move to config.py file
DEFAULT_BLUEPRINT_PATH = 'blueprint.yaml'
DEFAULT_INPUTS_PATH_FOR_INSTALL_COMMAND = 'inputs.yaml'
DEFAULT_TASK_THREAD_POOL_SIZE = 1
NO_VERBOSE = 0


class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return super(SmartFormatter, self)._split_lines(text, width)


def sub_parser_decorator(func=None, **parser_settings):
    if not func:
        return partial(sub_parser_decorator, **parser_settings)

    def wrapper(parser):
        sub_parser = parser.add_parser(**parser_settings)
        sub_parser.add_argument(
            '-v', '--verbose',
            dest='verbosity',
            action='count',
            default=NO_VERBOSE,
            help='Set verbosity level (can be passed multiple times)')
        sub_parser.add_argument(
            '-d', '--deployment-id',
            required=True,
            help='A unique ID for the deployment')
        func(sub_parser)
        return sub_parser
    return wrapper


def config_parser(parser=None):
    parser = parser or argparse.ArgumentParser(
        prog='Aria',
        description="Aria's Command Line Interface",
        formatter_class=SmartFormatter)
    parser.add_argument('-v', '--version', action='version')
    sub_parser = parser.add_subparsers(title='Commands', dest='command')
    add_init_parser(sub_parser)
    add_requirements_parser(sub_parser)
    add_install_parser(sub_parser)
    add_uninstall_parser(sub_parser)
    add_plugins_parser(sub_parser)
    add_execute_parser(sub_parser)
    add_instances_parser(sub_parser)
    add_output_parser(sub_parser)
    return parser


@sub_parser_decorator(
    name='init',
    help='Initialize environment',
    formatter_class=SmartFormatter)
def add_init_parser(init):
    init.add_argument(
        '-p', '--blueprint-path',
        dest='blueprint_path',
        required=True,
        help='The path to the desired blueprint')
    init.add_argument(
        '-i', '--inputs',
        dest='input',
        action='append',
        help='R|Inputs for the local workflow creation \n'
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files, \n'
             'a JSON string or as "key1=value1;key2=value2"). \n'
             'This argument can be used multiple times')
    init.add_argument(
        '--install-plugins',
        dest='install_plugins',
        action='store_true',
        help='Install the necessary plugins for the given blueprint')
    init.add_argument(
        '-b', '--blueprint-id',
        dest='blueprint_id',
        required=True,
        help='The blueprint ID'
    )


@sub_parser_decorator(
    name='requirements',
    help='Create a pip-compliant requirements file for a given blueprint',
    formatter_class=SmartFormatter)
def add_requirements_parser(requirements):
    requirements.add_argument(
        '-p', '--blueprint-path',
        dest='blueprint_path',
        required=True,
        help='The path to the desired blueprint')
    requirements.add_argument(
        '-o', '--output',
        dest='output',
        help='The local path for the requirements file')


@sub_parser_decorator(
    name='install',
    help='Install an application',
    formatter_class=SmartFormatter)
def add_install_parser(install):
    install.add_argument(
        '-p', '--blueprint-path',
        dest='blueprint_path',
        default=DEFAULT_BLUEPRINT_PATH,
        help="The path to the application's blueprint file. "
             "[default: {0}]".format(DEFAULT_BLUEPRINT_PATH))
    install.add_argument(
        '-i', '--inputs',
        dest='input',
        action='append',
        default=DEFAULT_INPUTS_PATH_FOR_INSTALL_COMMAND,
        help='Inputs for the local deployment '
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files, '
             'a JSON string or as "key1=value1;key2=value2"). '
             'This argument can be used multiple times. '
             '[default: {0}]'.format(DEFAULT_INPUTS_PATH_FOR_INSTALL_COMMAND))
    install.add_argument(
        '--install-plugins',
        dest='install_plugins',
        action='store_true',
        help='Install the necessary plugins for the given blueprint')
    install.add_argument(
        '-w', '--workflow',
        default='install',
        dest='workflow_id',
        help='The workflow to execute [default: install]')
    install.add_argument(
        '--parameters',
        dest='parameters',
        action='append',
        help='Parameters for the workflow execution '
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files, '
             'a JSON string or as "key1=value1;key2=value2"). '
             'This argument can be used multiple times.')
    install.add_argument(
        '--allow-custom-parameters',
        dest='allow_custom_parameters',
        action='store_true',
        help='Allow passing custom parameters ('
             'which were not defined in the workflows schema '
             'in the blueprint) to the execution.')
    install.add_argument(
        '--task-retries',
        dest='task_retries',
        default=0,
        type=int,
        help='How many times should a task be retried in case of failure')
    install.add_argument(
        '--task-retry-interval',
        dest='task_retry_interval',
        default=1,
        type=int,
        help='How many seconds to wait before each task is retried')
    install.add_argument(
        '--task-thread-pool-size',
        dest='task_thread_pool_size',
        default=DEFAULT_TASK_THREAD_POOL_SIZE,
        type=int,
        help='The size of the thread pool to execute tasks in')


@sub_parser_decorator(
    name='uninstall',
    help='Uninstall an application',
    formatter_class=SmartFormatter)
def add_uninstall_parser(uninstall):
    uninstall.add_argument(
        '-w', '--workflow',
        default='uninstall',
        dest='workflow_id',
        help='The workflow to execute [default: uninstall]')
    uninstall.add_argument(
        '--parameters',
        dest='parameters',
        action='append',
        help='Parameters for the workflow execution '
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files, '
             'a JSON string or as "key1=value1;key2=value2"). '
             'This argument can be used multiple times.')
    uninstall.add_argument(
        '--allow-custom-parameters',
        dest='allow_custom_parameters',
        action='store_true',
        help='Allow passing custom parameters ('
             'which were not defined in the workflows schema '
             'in the blueprint) to the execution.')
    uninstall.add_argument(
        '--task-retries',
        dest='task_retries',
        default=0,
        type=int,
        help='How many times should a task be retried in case of failure')
    uninstall.add_argument(
        '--task-retry-interval',
        dest='task_retry_interval',
        default=1,
        type=int,
        help='How many seconds to wait before each task is retried')
    uninstall.add_argument(
        '--task-thread-pool-size',
        dest='task_thread_pool_size',
        default=DEFAULT_TASK_THREAD_POOL_SIZE,
        type=int,
        help='The size of the thread pool to execute tasks in')


@sub_parser_decorator(
    name='plugins',
    help='Install the necessary plugins for a given blueprint',
    formatter_class=SmartFormatter)
def add_plugins_parser(plugins):
    plugins.add_argument(
        '-p', '--blueprint-path',
        dest='blueprint_path',
        help='The path to the desired blueprint')


@sub_parser_decorator(
    name='execute',
    help='Execute a workflow',
    formatter_class=SmartFormatter)
def add_execute_parser(execute):
    execute.add_argument(
        '-w', '--workflow',
        dest='workflow_id',
        help='The workflow to execute')
    execute.add_argument(
        '-p', '--parameters',
        dest='parameters',
        action='append',
        help='R|Parameters for the workflow execution\n'
             '(Can be provided as wildcard based paths (*.yaml, etc..) to YAML files,\n'
             'a JSON string or as "key1=value1;key2=value2").\n'
             'This argument can be used multiple times.')
    execute.add_argument(
        '--allow-custom-parameters',
        dest='allow_custom_parameters',
        action='store_true',
        help='Allow passing custom parameters '
             '(which were not defined in the workflows schema in the blueprint) '
             'to the execution.')
    execute.add_argument(
        '--task-retries',
        dest='task_retries',
        type=int,
        help='How many times should a task be retried in case of failure')
    execute.add_argument(
        '--task-retry-interval',
        dest='task_retry_interval',
        default=1,
        type=int,
        help='How many seconds to wait before each task is retried')
    execute.add_argument(
        '--task-thread-pool-size',
        dest='task_thread_pool_size',
        default=DEFAULT_TASK_THREAD_POOL_SIZE or cpu_count(),
        type=int,
        help='The size of the thread pool to execute tasks in')


@sub_parser_decorator(
    name='instances',
    help='Display node-instances for the execution',
    formatter_class=SmartFormatter)
def add_instances_parser(instances):
    instances.add_argument(
        '--node-id',
        help='Display node-instances only for this node')


@sub_parser_decorator(
    name='output',
    help='Display outputs for the execution',
    formatter_class=SmartFormatter)
def add_output_parser(output):
    pass

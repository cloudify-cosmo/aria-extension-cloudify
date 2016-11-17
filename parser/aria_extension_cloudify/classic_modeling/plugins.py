#
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved.
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

from .elements import find_by_name
from .nodes import find_hosted_node_templates
from aria import InvalidValueError
from aria.validation import Issue
from aria.utils import safe_repr
from collections import OrderedDict
import os

CENTRAL_DEPLOYMENT_AGENT = 'central_deployment_agent'
HOST_AGENT = 'host_agent'
SCRIPT_PLUGIN_NAME = 'script'
SCRIPT_RUNNER_RUN_OPERATION = 'script_runner.tasks.run'
SCRIPT_RUNNER_EXECUTE_WORKFLOW_OPERATION = 'script_runner.tasks.execute_workflow'

def plugins_to_install_for_operations(context, operations, agent):
    """
    Returns a list of all plugins referred to by the operations for the particular executor (agent).
    """
    
    plugin_names_to_install = []
    for operation in operations.itervalues():
        plugin_name, plugin_executor, _, _ = parse_implementation(context, operation.implementation)
        executor = operation.executor or plugin_executor
        if executor == agent:
            if plugin_name not in plugin_names_to_install: 
                plugin_names_to_install.append(plugin_name)
    return [_find_plugin(context, v) for v in plugin_names_to_install]

def add_plugins_to_install_for_node_template(context, node_template, plugins_to_install, deployment_plugins_to_install):
    """
    Gathers plugins referred to by the operations of the template's and its relationships' source interfaces. This is done for the
    central deployment agent, and if we are a compute node template also for the host agent. Also, if we are a compute node template,
    then we will continue gathering following the path of contained-in relationships.
    """
    
    _add_plugins_to_install_for_interface(context, plugins_to_install, node_template.interface_templates, HOST_AGENT)
    _add_plugins_to_install_for_interface(context, deployment_plugins_to_install, node_template.interface_templates, CENTRAL_DEPLOYMENT_AGENT)

    # Plugins from relationships' source interfaces
    for requirement in node_template.requirement_templates:
        if requirement.relationship_template is not None:
            _add_plugins_to_install_for_interface(context, plugins_to_install, requirement.relationship_template.source_interface_templates, HOST_AGENT)
            _add_plugins_to_install_for_interface(context, deployment_plugins_to_install, requirement.relationship_template.source_interface_templates, CENTRAL_DEPLOYMENT_AGENT)

    # Recurse into hosted node templates
    for t in find_hosted_node_templates(context, node_template):
        add_plugins_to_install_for_node_template(context, t, plugins_to_install, deployment_plugins_to_install)

def is_file(context, name):
    """
    Returns True if the name points to a file under one of our loading prefixes.
    """
    
    for prefix in context.loading.prefixes:
        path = os.path.join(prefix, name)
        if os.path.isfile(path):
            return True
    return False

def parse_implementation(context, implementation, is_workflow=False):
    """
    Parses an operation's :code:`implementation` string, differentiating between references Python plugin functions
    (in the plugin-dot-function format) and relative paths to script files to be executed by the script runner plugins.
    
    Note that workflow operations use a special script runner plugin.
    """
    
    parsed = False

    if not implementation:
        plugin_name = None
        plugin_executor = None
        operation_name = None
        inputs = OrderedDict()
        parsed = True
    
    if not parsed:
        if is_file(context, implementation):
            # Explicit script
            plugin = _find_plugin(context, SCRIPT_PLUGIN_NAME)
            plugin_name = plugin['name'] 
            plugin_executor = plugin['executor']
            if is_workflow:
                operation_name = SCRIPT_RUNNER_EXECUTE_WORKFLOW_OPERATION
                inputs = OrderedDict((
                    ('script_path', OrderedDict((('default', implementation),))),)) 
            else:
                operation_name = SCRIPT_RUNNER_RUN_OPERATION
                inputs = OrderedDict((('script_path', implementation),))
            parsed = True

    if not parsed:
        # plugin.operation
        plugin, operation_name = _parse_implementation(context, implementation)
        plugin_name = plugin['name'] 
        plugin_executor = plugin['executor']
        inputs = OrderedDict()

    return plugin_name, plugin_executor, operation_name, inputs

#
# Utils
#

def _find_plugin(context, name):
    for plugin in context.modeling.plugins:
        if plugin['name'] == name:
            return plugin
    raise InvalidValueError('can\'t find plugin: %s' % safe_repr(name), level=Issue.BETWEEN_TYPES)

def _parse_implementation(context, implementation):
    plugins = []
    
    for plugin in context.modeling.plugins:
        if implementation.startswith(plugin['name'] + '.'):
            plugins.append(plugin)
            
    length = len(plugins)
    if length > 1:
        raise InvalidValueError('ambiguous plugin name in implementation: %s' % safe_repr(implementation), level=Issue.BETWEEN_TYPES)
    elif length == 1:
        plugin = plugins[0]
        operation = implementation[len(plugin['name']) + 1:]
        if not operation:
            raise InvalidValueError('no operation name in implementation: %s' % safe_repr(implementation), level=Issue.BETWEEN_TYPES)
        return plugin, operation
    elif context.modeling.plugins:
        plugin = context.modeling.plugins[0]
        return plugin, implementation
    raise InvalidValueError('unknown plugin for implementation: %s' % safe_repr(implementation), level=Issue.BETWEEN_TYPES)

def _add_plugins_to_install_for_interface(context, plugins_to_install, interfaces, agent):
    for interface in interfaces.itervalues():
        for operation in interface.operation_templates.itervalues():
            plugin_name, plugin_executor, _, _ = parse_implementation(context, operation.implementation)
            executor = operation.executor or plugin_executor
            if executor == agent:
                if find_by_name(plugins_to_install, plugin_name) is None: 
                    plugins_to_install.append(_find_plugin(context, plugin_name))

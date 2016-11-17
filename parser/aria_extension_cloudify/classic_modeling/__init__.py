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

from .elements import find_by_name, get_type_parent_name
from .parameters import has_intrinsic_functions
from .nodes import is_host, find_host_node_template, find_host_node
from .groups import find_groups, iter_scaling_groups, prune_redundant_members
from .relationships import is_contained_in
from .plugins import CENTRAL_DEPLOYMENT_AGENT, SCRIPT_PLUGIN_NAME, plugins_to_install_for_operations, add_plugins_to_install_for_node_template, parse_implementation, is_file
from .policies import SCALING_POLICY_NAME
from aria import InvalidValueError
from aria.consumption import Consumer
from aria.validation import Issue
from aria.utils import as_raw, as_agnostic, merge, prune, json_dumps, string_list_as_string, safe_repr
from collections import OrderedDict

class ClassicDeploymentPlan(Consumer):
    """
    Generates the classic deployment plan based on the service instance.
    """

    def consume(self):
        if self.context.modeling.instance is None:
            self.context.validation.report('ClassicDeploymentPlan consumer: missing deployment plan')
            return

        plugins = self.context.presentation.get('service_template', 'plugins')
        plugins = [convert_plugin(self.context, v) for v in plugins.itervalues()] if plugins is not None else []
        setattr(self.context.modeling, 'plugins', plugins)

        deployment_plan = convert_instance(self.context)
        setattr(self.context.modeling, 'classic_deployment_plan', deployment_plan)
    
    def dump(self):
        indent = self.context.get_arg_value_int('indent', 2)
        self.context.write(json_dumps(self.context.modeling.classic_deployment_plan_ordered, indent=indent))

#
# Conversions
#

def convert_instance(context):
    r = OrderedDict((
        # Meta
        ('version',
            convert_version(context)),
        ('description', context.modeling.instance.description),
        
        # General
        ('inputs',
            convert_parameter_defaults(context, context.modeling.instance.inputs)),
        ('outputs',
            convert_parameter_values(context, context.modeling.instance.outputs)),
        ('workflows', OrderedDict(
            (k, convert_workflow(context, v)) for k, v in context.modeling.instance.operations.iteritems())),
        
        # Plugins
        ('deployment_plugins_to_install',
            []),
        ('workflow_plugins_to_install',
            plugins_to_install_for_operations(context, context.modeling.instance.operations, CENTRAL_DEPLOYMENT_AGENT)),

        # Instances
        ('node_instances',
            [convert_node(context, v) for v in context.modeling.instance.nodes.itervalues()]),

        # Templates
        ('nodes',
            [convert_node_template(context, v) for v in context.modeling.model.node_templates.itervalues()]),
        ('groups', OrderedDict(
            (k, convert_group_template(context, v)) for k, v in context.modeling.model.group_templates.iteritems())),
        ('scaling_groups', OrderedDict(
            (k, convert_group_template(context, v, policy_template)) for k, v, policy_template in iter_scaling_groups(context))),
        ('policies', OrderedDict(
            (k, convert_policy_template(context, v)) for k, v in context.modeling.model.policy_templates.iteritems())),

        # Types
        ('policy_types', OrderedDict(
            (v.name, convert_policy_type(context, v)) for v in context.modeling.policy_types.iter_descendants() if v.name != SCALING_POLICY_NAME)),
        ('policy_triggers', OrderedDict(
            (v.name, convert_policy_trigger_type(context, v)) for v in context.modeling.policy_trigger_types.iter_descendants())),
        ('relationships', OrderedDict(
            (v.name, convert_relationship_type(context, v)) for v in context.modeling.relationship_types.iter_descendants()))))

    # Gather 'deployment_plugins_to_install' from node templates
    for node in r['nodes']:
        node_deployment_plugins_to_install = node.get('deployment_plugins_to_install')
        if node_deployment_plugins_to_install:
            for plugin in node_deployment_plugins_to_install:
                if find_by_name(r['deployment_plugins_to_install'], plugin['name']) is None:
                    r['deployment_plugins_to_install'].append(plugin)

    add_deployment_plan_attributes(r)
    
    return r

def add_deployment_plan_attributes(deployment_plan):
    # Some code needs to access these as Python attributes
    setattr(deployment_plan, 'version', deployment_plan['version'])
    setattr(deployment_plan['version'], 'definitions_name', deployment_plan['version']['definitions_name'])
    setattr(deployment_plan['version'], 'definitions_version', deployment_plan['version']['definitions_version'])
    setattr(deployment_plan['version']['definitions_version'], 'number', deployment_plan['version']['definitions_version']['number'])
    setattr(deployment_plan, 'inputs', deployment_plan['inputs'])
    setattr(deployment_plan, 'outputs', deployment_plan['outputs'])
    setattr(deployment_plan, 'node_templates', deployment_plan['nodes'])

#
# Plugins
#

def convert_plugin(context, plugin):
    return OrderedDict((
        ('name', plugin._name),
        ('distribution', getattr(plugin, 'distribution', None)),
        ('distribution_release', getattr(plugin, 'distribution_release', None)),
        ('distribution_version', getattr(plugin, 'distribution_version', None)),
        ('executor', plugin.executor),
        ('install', plugin.install),
        ('install_arguments', getattr(plugin, 'install_arguments', None)),
        ('package_name', getattr(plugin, 'package_name', None)),
        ('package_version', getattr(plugin, 'package_version', None)),
        ('source', plugin.source),
        ('supported_platform', getattr(plugin, 'supported_platform', None))))

#
# Meta
#

def convert_version(context):
    # The version number as a tuple of integers
    number = context.presentation.get('service_template', 'tosca_definitions_version')
    number = number[len('cloudify_dsl_'):]
    number = number.split('_')
    number = tuple(int(v) for v in number)

    return OrderedDict((
        ('definitions_name', 'cloudify_dsl'),
        ('definitions_version', OrderedDict((
            ('number', number),)))))

#
# General
#

def convert_workflow(context, operation):
    plugin_name, _, operation_name, inputs = parse_implementation(context, operation.implementation, True)

    r = OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('parameters', merge(convert_parameter_defaults(context, operation.inputs), inputs)),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

    return r

#
# Instances
#

def convert_node(context, node):
    # Host
    host_node = find_host_node(context, node)
    
    # Groups
    groups = find_groups(context, node)

    return OrderedDict((
        ('id', node.id),
        ('name', node.template_name),
        ('relationships', [convert_relationship(context, v) for v in node.relationships]),
        ('host_id', host_node.id if host_node is not None else None),
        ('scaling_groups', [OrderedDict((('name', group.template_name),)) for group in groups])))

def convert_relationship(context, relationship):
    target_node = context.modeling.instance.nodes.get(relationship.target_node_id)
    
    return OrderedDict((
        ('type', relationship.type_name), # template_name?
        ('target_id', relationship.target_node_id),
        ('target_name', target_node.template_name)))

#
# Templates
#

def convert_node_template(context, node_template):
    node_type = context.modeling.node_types.get_descendant(node_template.type_name)
    
    # Host
    host_node_template = find_host_node_template(context, node_template)
    is_a_host = is_host(context, node_template)
    
    # Count instances
    current_instances = 0
    for node in context.modeling.instance.nodes.itervalues():
        if node.template_name == node_template.name:
            current_instances += 1

    # Plugins to install
    plugins_to_install = []
    deployment_plugins_to_install = []
    add_plugins_to_install_for_node_template(context, node_template, plugins_to_install, deployment_plugins_to_install)
    
    if plugins_to_install and not is_a_host:
        raise InvalidValueError('node template "%s" has plugins to install but is not a host: %s' % (node_template.name, string_list_as_string(v['name'] for v in plugins_to_install)), level=Issue.BETWEEN_TYPES)
    
    # Relationships
    relationships = []
    contained_in = 0
    for requirement in node_template.requirement_templates:
        if requirement.relationship_template is not None:
            if is_contained_in(context, requirement.relationship_template):
                contained_in += 1
            relationships.append(convert_relationship_template(context, requirement))
            if contained_in > 1:
                raise InvalidValueError('node template "%s" has more than one contained-in relationship' % node_template.name, level=Issue.BETWEEN_TYPES)
    
    for relationship in relationships:
        if relationship['target_id'] == node_template.name:
            raise InvalidValueError('node template "%s" has a "%s" relationship to itself' % (node_template.name, relationship['type']), level=Issue.BETWEEN_TYPES)

    r = OrderedDict((
        ('name', node_template.name),
        ('id', node_template.name),
        ('type', node_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, node_type, context.modeling.node_types)),
        ('properties', convert_properties(context, node_template.properties)),
        ('capabilities', OrderedDict((
            ('scalable', OrderedDict((
                ('properties', OrderedDict((
                    ('current_instances', current_instances),
                    ('default_instances', node_template.default_instances),
                    ('min_instances', node_template.min_instances),
                    ('max_instances', node_template.max_instances if node_template.max_instances is not None else -1)))),))),))),
        ('operations', convert_operations(context, node_template.interface_templates)),
        ('relationships', relationships),
        ('host_id', host_node_template.name if host_node_template is not None else None),
        ('plugins', context.modeling.plugins),
        ('plugins_to_install', plugins_to_install),
        ('deployment_plugins_to_install', deployment_plugins_to_install)))
    
    # Prune some fields
    if host_node_template is None:
        del r['host_id']
    if not is_a_host:
        del r['plugins_to_install']
        
    return r

def convert_relationship_template(context, requirement):
    relationship_template = requirement.relationship_template
    relationship_type = context.modeling.relationship_types.get_descendant(relationship_template.type_name)

    return OrderedDict((
        ('type', relationship_type.name),
        ('type_hierarchy', convert_type_hierarchy(context, relationship_type, context.modeling.relationship_types)),
        ('target_id', requirement.target_node_template_name),
        ('properties', convert_properties(context, relationship_template.properties)),
        ('source_interfaces', convert_interfaces(context, relationship_template.source_interface_templates)),
        ('target_interfaces', convert_interfaces(context, relationship_template.target_interface_templates)),
        ('source_operations', convert_operations(context, relationship_template.source_interface_templates)), 
        ('target_operations', convert_operations(context, relationship_template.target_interface_templates))))

def convert_group_template(context, group_template, policy_template=None):
    # Members
    node_members = set(group_template.member_node_template_names)
    group_members = set(group_template.member_group_template_names)
    prune_redundant_members(context, node_members, group_members)
    members = list(node_members | group_members)
    
    if not members:
        raise InvalidValueError('group "%s" has no members' % group_template.name, level=Issue.BETWEEN_TYPES)

    r = OrderedDict((
        ('members', members),
        ('policies', OrderedDict(
            (k, convert_group_policy(context, v)) for k, v in group_template.policy_templates.iteritems()))))

    # For scaling groups
    if policy_template is not None:
        r['properties'] = convert_properties(context, policy_template.properties)

    return r

def convert_group_policy(context, group_policy):
    return OrderedDict((
        ('type', group_policy.type_name),
        ('properties', convert_properties(context, group_policy.properties)),
        ('triggers', OrderedDict(
            (k, convert_group_policy_trigger(context, v)) for k, v in group_policy.triggers.iteritems()))))

def convert_group_policy_trigger(context, group_policy_trigger):
    return OrderedDict((
        ('source', group_policy_trigger.implementation),
        ('parameters', convert_properties(context, group_policy_trigger.properties))))

def convert_policy_template(context, policy_template):
    return OrderedDict((
        ('properties', convert_properties(context, policy_template.properties)),))

#
# Types
#

def convert_policy_type(context, policy_type):
    return OrderedDict((
        ('source', policy_type.implementation),
        ('properties', convert_parameter_defaults(context, policy_type.properties))))

def convert_policy_trigger_type(context, policy_trigger_type):
    return OrderedDict((
        ('source', policy_trigger_type.implementation),
        ('parameters', convert_parameter_defaults(context, policy_trigger_type.properties))))

def convert_relationship_type(context, relationship_type):
    r = OrderedDict((
        ('name', relationship_type.name),
        ('derived_from', get_type_parent_name(relationship_type, context.modeling.relationship_types)),
        ('type_hierarchy', convert_type_hierarchy(context, relationship_type, context.modeling.relationship_types)),
        ('properties', convert_parameter_defaults(context, relationship_type.properties)),
        ('source_interfaces', convert_interfaces(context, relationship_type.source_interfaces)),
        ('target_interfaces', convert_interfaces(context, relationship_type.target_interfaces))))
    
    # Prune some fields
    if r['derived_from'] is None:
        del r['derived_from']
    
    return r

#
# Misc
#

def convert_properties(context, properties):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in properties.iteritems()))

def convert_parameter_defaults(context, parameters):
    return OrderedDict((
        (k, convert_parameter_default(context, v)) for k, v in parameters.iteritems()))

def convert_parameter_default(context, parameter):
    # prune removes any None (but not NULL), and then as_raw converts any NULL to None
    return as_raw(prune(OrderedDict((
        ('type', parameter.type_name),
        ('default', parameter.value),
        ('description', parameter.description)))))

def convert_parameter_values(context, values):
    return OrderedDict((
        (k, convert_parameter_value(context, v)) for k, v in values.iteritems()))

def convert_parameter_value(context, value):
    # prune removes any None (but not NULL), and then as_raw converts any NULL to None
    return as_raw(prune(OrderedDict((
        ('type', value.type_name),
        ('value', value.value),
        ('description', value.description)))))

def convert_interfaces(context, interfaces):
    r = OrderedDict()

    for interface_name, interface in interfaces.iteritems():
        rr = OrderedDict()
        for operation_name, operation in interface.operation_templates.iteritems():
            rr[operation_name] = convert_interface_operation(context, operation)
        r[interface_name] = rr
    
    return r

def convert_interface_operation(context, operation):
    _, plugin_executor, _, _ = parse_implementation(context, operation.implementation)
    
    return OrderedDict((
        ('implementation', operation.implementation or ''),
        ('inputs', convert_inputs(context, operation.inputs)),
        ('executor', operation.executor or plugin_executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

def convert_operations(context, interfaces):
    r = OrderedDict()
    
    # We support both long-form (interface-dot-operation) and short-form (just the operation)
    duplicate_operation_names = set()
    for interface_name, interface in interfaces.iteritems():
        for operation_name, operation in interface.operation_templates.iteritems():
            operation = convert_operation(context, operation)
            r['%s.%s' % (interface_name, operation_name)] = operation # long-form name
            if operation_name not in r:
                r[operation_name] = operation # short-form name 
            else:
                duplicate_operation_names.add(operation_name)

    # If the short-form name is not unique, then we should not have it at all 
    for operation_name in duplicate_operation_names:
        del r[operation_name]
            
    return r

def convert_operation(context, operation):
    plugin_name, plugin_executor, operation_name, inputs = parse_implementation(context, operation.implementation)

    inputs = merge(inputs, convert_inputs(context, operation.inputs))

    if plugin_name == SCRIPT_PLUGIN_NAME:
        script_path = inputs.get('script_path')
        if script_path and (not is_file(context, script_path)):
            raise InvalidValueError('"script_path" input for "script" plugin does not refer to a file: %s' % safe_repr(script_path), level=Issue.BETWEEN_TYPES)

    return OrderedDict((
        ('plugin', plugin_name),
        ('operation', operation_name),
        ('inputs', inputs),
        ('has_intrinsic_functions', has_intrinsic_functions(context, operation.inputs)),
        ('executor', operation.executor or plugin_executor),
        ('max_retries', operation.max_retries),
        ('retry_interval', operation.retry_interval)))

def convert_inputs(context, inputs):
    return OrderedDict((
        (k, as_raw(v.value)) for k, v in inputs.iteritems()))

def convert_type_hierarchy(context, the_type, hierarchy):
    """
    List of types in sequence from ancestor to our type.
    """ 
    
    type_hierarchy = []
    while (the_type is not None) and (the_type.name is not None):
        type_hierarchy.insert(0, the_type.name)
        the_type = hierarchy.get_parent(the_type.name)
    return type_hierarchy

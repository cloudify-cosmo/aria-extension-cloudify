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

"""
Aria's deployment Package
Path: aria.deployment

Methods:
    * modify_deployment
    * prepare_deployment_plan

"""

from ..exceptions import UnknownInputError
from ..parser.models import Plan
from ..parser.scan import scan_service_template
from ..parser.framework.functions import plan_evaluation_handler
from .exceptions import MissingRequiredInputError


from .relationships_graph import (
    build_node_graph,
    build_deployment_node_graph,
    extract_node_instances,
    build_previous_deployment_node_graph,
    extract_added_node_instances,
    extract_removed_node_instances,
    extract_added_relationships,
    extract_removed_relationships,
)

__all__ = [
    'modify_deployment',
    'prepare_deployment_plan',
]


def prepare_deployment_plan(plan, inputs=None):
    """
    Prepare a plan for deployment
    :param plan:
    :type plan (Plan, dict)
    :param inputs:
    :return:
    """
    if not isinstance(plan, dict):
        raise TypeError(
            'plan arg mast be a dict or Plan type, got: {0} [{1}]'.format(
                plan, type(plan)))
    if not isinstance(plan, Plan):
        plan = Plan(plan)
    _set_plan_inputs(plan, inputs)
    _process_functions(plan)
    return _create_deployment(plan)


def modify_deployment(
        nodes,
        previous_nodes,
        previous_node_instances,
        modified_nodes,
        scaling_groups):
    """
    modifies deployment according to the expected nodes.
    based on previous_node_instances
    Prepare a modify plan for deployment
    :param nodes: the entire set of expected nodes.
    :param previous_nodes:
    :param previous_node_instances:
    :param modified_nodes: existing nodes whose instance number has changed
        Add a line note
    :param scaling_groups:
    :return: a dict of add,extended,reduced and removed instances
        Add a line note
    """
    plan_node_graph = build_node_graph(
        nodes=nodes,
        scaling_groups=scaling_groups)
    previous_plan_node_graph = build_node_graph(
        nodes=previous_nodes,
        scaling_groups=scaling_groups)
    previous_deployment_node_graph, previous_deployment_contained_graph = ( # pylint: disable=invalid-name
        build_previous_deployment_node_graph(
            plan_node_graph=previous_plan_node_graph,
            previous_node_instances=previous_node_instances))
    new_deployment_node_graph, ctx = build_deployment_node_graph(
        plan_node_graph=plan_node_graph,
        previous_deployment_node_graph=previous_deployment_node_graph,
        previous_deployment_contained_graph=previous_deployment_contained_graph,
        modified_nodes=modified_nodes)

    # Any node instances which were added or removed
    added_and_related = extract_added_node_instances(
        previous_deployment_node_graph,
        new_deployment_node_graph,
        ctx=ctx)
    removed_and_related = extract_removed_node_instances(
        previous_deployment_node_graph,
        new_deployment_node_graph,
        ctx=ctx)

    # Any node instances which had a modification to their relationship.
    # (newly introduced and removed nodes)
    extended_and_related = extract_added_relationships(
        previous_deployment_node_graph,
        new_deployment_node_graph,
        ctx=ctx)
    reduced_and_related = extract_removed_relationships(
        previous_deployment_node_graph,
        new_deployment_node_graph,
        ctx=ctx)

    # The extracted extended and reduced relationships hold the new and old
    # node instances. These are not required, since the change is on
    # node instance level (and not the relationship level)
    return {
        'added_and_related': added_and_related,
        'extended_and_related': _filter_out_node_instances(
            added_and_related, extended_and_related),
        'reduced_and_related': _filter_out_node_instances(
            removed_and_related, reduced_and_related),
        'removed_and_related': removed_and_related,
    }


def _create_deployment(plan):
    """
    Expand node instances based on number of instances to deploy and
    defined relationships
    """
    plan_node_graph = build_node_graph(
        nodes=plan['nodes'], scaling_groups=plan['scaling_groups'])

    deployment_node_graph, ctx = build_deployment_node_graph(plan_node_graph)

    plan['node_instances'] = extract_node_instances(
        node_instances_graph=deployment_node_graph,
        ctx=ctx)

    return plan


def _set_plan_inputs(plan, inputs=None):
    inputs = inputs or {}
    missing_inputs = _missing_inputs(plan, inputs)
    if missing_inputs:
        raise MissingRequiredInputError(
            'Required inputs {0} were not specified - expected '
            'inputs: {1}'.format(missing_inputs, plan['inputs'].keys()))

    not_expected = _not_expected_inputs(inputs, plan)
    if not_expected:
        raise UnknownInputError(
            'Unknown inputs {0} specified - '
            'expected inputs: {1}'.format(
                not_expected, plan['inputs'].keys()))

    plan['inputs'] = inputs


def _missing_inputs(plan, inputs):
    missing_inputs = []
    for input_name, input_def in plan['inputs'].iteritems():
        if input_name not in inputs:
            if 'default' in input_def and input_def['default'] is not None:
                inputs[input_name] = input_def['default']
            else:
                missing_inputs.append(input_name)
    return missing_inputs


def _not_expected_inputs(inputs, plan):
    return [input_name for input_name in inputs.keys()
            if input_name not in plan['inputs']]


def _process_functions(plan):
    handler = plan_evaluation_handler(plan)
    scan_service_template(plan, handler, replace=True)


def _filter_out_node_instances(node_instances_to_filter_out, base_node_instances):
    instance_ids_to_remove = set(
        node['id']
        for node in node_instances_to_filter_out
        if 'modification' in node)
    return [
        node
        for node in base_node_instances
        if node['id'] not in instance_ids_to_remove]

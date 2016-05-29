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

NODE_INSTANCES = 'node_instances'


def create_deployment_plan(plan):
    """
    Expand node instances based on number of instances to deploy and
    defined relationships
    """
    plan_node_graph = build_node_graph(
        nodes=plan['nodes'],
        scaling_groups=plan['scaling_groups'])

    deployment_node_graph, ctx = build_deployment_node_graph(
        plan_node_graph)

    node_instances = extract_node_instances(
        node_instances_graph=deployment_node_graph,
        ctx=ctx)

    plan[NODE_INSTANCES] = node_instances
    return plan


def modify_deployment(
        nodes,
        previous_nodes,
        previous_node_instances,
        modified_nodes,
        scaling_groups):
    """
    modifies deployment according to the expected nodes. based on
    previous_node_instances
    """
    plan_node_graph = build_node_graph(
        nodes=nodes,
        scaling_groups=scaling_groups)
    previous_plan_node_graph = build_node_graph(
        nodes=previous_nodes,
        scaling_groups=scaling_groups)
    previous_deployment_node_graph, previous_deployment_contained_graph = (  # pylint: disable=invalid-name
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
    return {
        'added_and_related': added_and_related,
        'extended_and_related': extended_and_related,
        'reduced_and_related': reduced_and_related,
        'removed_and_related': removed_and_related,
    }


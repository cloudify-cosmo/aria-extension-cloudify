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

from itertools import groupby

from aria.deployment.relationships_graph import (
    build_node_graph,
    build_previous_deployment_node_graph,
)
from aria.deployment import modify_deployment_plan
from ...suite import PrepareDeploymentPlanTestCase


class BaseTestMultiInstance(PrepareDeploymentPlanTestCase):
    BASE_BLUEPRINT = """
node_types:
    tosca.nodes.Compute:
        properties:
            x:
                default: y
    db: {}
    webserver: {}
    db_dependent: {}
    type: {}
    network: {}
relationships:
    test_relationship: {}
    tosca.relationships.DependsOn:
        properties:
            connection_type:
                default: 'all_to_all'
    tosca.relationships.HostedOn:
        derived_from: tosca.relationships.DependsOn
    tosca.relationships.ConnectsTo:
        derived_from: tosca.relationships.DependsOn

node_templates:
    """

    @staticmethod
    def relationships_by_target_name(relationships, name):
        return [
            rel for rel in relationships
            if rel['target_name'] == name]

    @staticmethod
    def nodes_by_name(nodes, name):
        return [
            node for node in nodes
            if node['name'] == name]

    @staticmethod
    def node_ids(nodes):
        return [node['id'] for node in nodes]

    @staticmethod
    def nodes_relationships(nodes, target_name=None):
        return [
            rel
            for node in nodes
            for rel in node['relationships']
            if not target_name or rel['target_name'] == target_name
            ]

    @staticmethod
    def modify_multi(plan, modified_nodes):
        return modify_deployment_plan(
            nodes=plan['nodes'],
            previous_nodes=plan['nodes'],
            previous_node_instances=plan['node_instances'],
            modified_nodes=modified_nodes,
            scaling_groups=plan['scaling_groups'])

    def assert_each_node_valid_hosted(self, nodes, hosts):
        node_ids, host_ids = self.node_ids(nodes), self.node_ids(hosts)

        self.assertEqual(len(node_ids) % len(host_ids), 0)
        self.assertEqual(len(node_ids), len(set(node_ids)))
        for node in nodes:
            self.assertIn(node['host_id'], host_ids)

        def key_function(key):
            return key['host_id']

        for _, group in groupby(sorted(nodes, key=key_function), key=key_function):
            self.assertEqual(
                sum(1 for _ in group), len(node_ids) / len(host_ids))

    def assert_contained(self, source_relationships, node_ids, target_name):
        relationships = self.relationships_by_target_name(
            source_relationships, target_name)
        target_ids = [rel['target_id'] for rel in relationships]

        self.assertEqual(set(node_ids), set(target_ids))

    def assert_all_to_one(self, source_relationships, node_ids, target_name):
        relationships = self.relationships_by_target_name(
            source_relationships, target_name)
        target_ids = [rel['target_id'] for rel in relationships]

        self.assertEqual(1, len(set(target_ids)))
        self.assertIn(target_ids[0], node_ids)
        return target_ids[0]

    def assert_all_to_all(self, source_relationships_lists, node_ids, target_name):
        relationships = self.relationships_by_target_name(
            source_relationships_lists, target_name)
        target_ids = (rel['target_id'] for rel in relationships)
        self.assertEqual(set(node_ids), set(target_ids))

    def assert_added_not_in_previous(self, plan, modification):
        previous_node_instances = plan['node_instances']
        added_and_related = modification['added_and_related']

        plan_node_graph = build_node_graph(
            nodes=plan['nodes'],
            scaling_groups=plan['scaling_groups'])
        previous_graph, _ = build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=previous_node_instances)
        added_nodes_graph, _ = build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=added_and_related)

        for instance_id, data in added_nodes_graph.nodes_iter(data=True):
            instance = data['node']
            if instance.get('modification') == 'added':
                self.assertNotIn(instance_id, previous_graph)
                continue
            self.assertIn(instance_id, previous_graph)

        for source, target, in added_nodes_graph.edges_iter():
            self.assertFalse(previous_graph.has_edge(source, target))

    def assert_removed_in_previous(self, plan, modification):
        previous_node_instances = plan['node_instances']
        removed_and_related = modification['removed_and_related']

        plan_node_graph = build_node_graph(
            nodes=plan['nodes'],
            scaling_groups=plan['scaling_groups'])
        previous_graph, _ = build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=previous_node_instances)
        removed_nodes_graph, _ = build_previous_deployment_node_graph(
            plan_node_graph=plan_node_graph,
            previous_node_instances=removed_and_related)

        for instance_id, data in removed_nodes_graph.nodes_iter(data=True):
            self.assertIn(instance_id, previous_graph)
        for source, target, in removed_nodes_graph.edges_iter():
            self.assertTrue(previous_graph.has_edge(source, target))

    def assert_modification(
            self,
            modification,
            expected_added_and_related_count,
            expected_removed_and_related_count,
            expected_added_count,
            expected_removed_count):
        added_and_related = modification['added_and_related']
        removed_and_related = modification['removed_and_related']
        added = [instance for instance in added_and_related
                 if instance.get('modification') == 'added']
        removed = [instance for instance in removed_and_related
                   if instance.get('modification') == 'removed']

        # import ipdb; ipdb.set_trace()
        self.assertEqual(expected_added_and_related_count, len(added_and_related))
        self.assertEqual(expected_removed_and_related_count, len(removed_and_related))
        self.assertEqual(expected_added_count, len(added))
        self.assertEqual(expected_removed_count, len(removed))

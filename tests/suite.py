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

import os
from uuid import uuid4
from shutil import rmtree
from tempfile import mkdtemp
from itertools import imap, groupby
from yaml import safe_dump

from testtools import TestCase

from aria.parser import Parser
from aria.parser.dsl_supported_versions import (
    supported_versions,
    BASE_VERSION_PROFILE,
    add_version_to_database,
)
from aria.deployment.relationships_graph import (
    build_node_graph,
    build_previous_deployment_node_graph,
)
from aria.exceptions import DSLParsingException
from aria.deployment import prepare_deployment_plan, modify_deployment


class TempDirectoryTestCase(TestCase):
    temp_directory = None
    _path_to_uri = 'file://{0}'.format

    def setUp(self):
        self.temp_directory = mkdtemp(prefix=self.__class__.__name__)
        self.addCleanup(self.cleanup)
        super(TempDirectoryTestCase, self).setUp()

    def cleanup(self):
        rmtree(self.temp_directory, ignore_errors=True)

    def write_to_file(self, content, filename, directory=None):
        directory = os.path.join(self.temp_directory, directory or '')
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, filename)
        with open(file_path, 'w') as file_obj:
            file_obj.write(content)
        return file_path

    def make_yaml_file(self, content, as_uri=False):
        filename = 'tempfile{0}.yaml'.format(uuid4())
        path = self.write_to_file(content, filename)
        return path if not as_uri else self._path_to_uri(path)

    def create_yaml_with_imports(self, contents, as_uri=False):
        import_path_maker = (
            (lambda path: path)
            if as_uri else
            self._path_to_uri)

        def import_creator(content):
            path = self.make_yaml_file(content)
            return import_path_maker(path)

        return '\nimports:\n    -   {0}'.format(
            '\n    -   '.join(imap(import_creator, contents)))


class ParserTestCase(TestCase):
    template = None

    def setUp(self):
        self.template = Template()
        super(ParserTestCase, self).setUp()

    def parse(
            self,
            import_resolver=None,
            validate_version=True,
            dsl_location=None,
            template_inputs=None):
        parser = Parser(import_resolver=import_resolver,
                        validate_version=validate_version)
        if template_inputs:
            template = str(self.template) % template_inputs
        else:
            template = str(self.template)
        return parser.parse_from_string(template, dsl_location=dsl_location)

    def assert_parser_raise_exception(
            self,
            exception_types=DSLParsingException,
            error_code=None,
            extra_tests=()):
        try:
            self.parse()
            self.fail()
        except exception_types as exc:
            if error_code:
                self.assertEquals(error_code, exc.err_code)
            for test in extra_tests:
                test(exc)
        return exc


class PrepareDeploymentPlanTestCase(ParserTestCase):
    def prepare_deployment_plan(self, parse_kwargs=None, deployment_kwargs=None):
        plan = self.parse(**parse_kwargs or {})
        return prepare_deployment_plan(plan, **deployment_kwargs or {})

    def assert_prepare_deployment_raise_exception(
            self,
            exception_types,
            extra_tests=(),
            parse_kwargs=None,
            deployment_kwargs=None):
        try:
            self.prepare_deployment_plan(
                parse_kwargs=parse_kwargs or {},
                deployment_kwargs=deployment_kwargs or {})
            self.fail()
        except exception_types as exc:
            for test in extra_tests:
                test(exc)
        return exc


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
        return modify_deployment(
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

        for instance_id, _ in removed_nodes_graph.nodes_iter(data=True):
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

        self.assertEqual(expected_added_and_related_count, len(added_and_related))
        self.assertEqual(expected_removed_and_related_count, len(removed_and_related))
        self.assertEqual(expected_added_count, len(added))
        self.assertEqual(expected_removed_count, len(removed))


class Template(object):
    BASIC_NODE_TEMPLATES_SECTION = (
        '\nnode_templates:\n'
        '    test_node:\n'
        '        type: test_type\n'
        '        properties:\n'
        '            key: "val"\n'
    )
    BASIC_PLUGIN = (
        '\nplugins:\n'
        '    test_plugin:\n'
        '        source: dummy\n'
    )

    BASIC_TYPE = (
        '\nnode_types:\n'
        '    test_type:\n'
        '        interfaces:\n'
        '            test_interface1:\n'
        '                install:\n'
        '                    implementation: test_plugin.install\n'
        '                    inputs: {}\n'
        '                terminate:\n'
        '                    implementation: test_plugin.terminate\n'
        '                    inputs: {}\n'
        '        properties:\n'
        '            install_agent:\n'
        '               default: "false"\n'
        '            key: {}\n'
    )

    PLUGIN_WITH_INSTALL_ARGS = (
        '\nplugins:\n'
        '    test_plugin:\n'
        '        source: dummy\n'
        '        install_arguments: -r requirements.txt\n'
    )

    def __init__(self):
        self.clear()

    def __str__(self):
        return self.template

    def __iadd__(self, other):
        self.template += other
        return self

    def from_members(
            self,
            groups=None,
            nodes=None,
            policies=None,
            policy_types=None,
            version=None):
        groups = groups or {}
        nodes = nodes or {'node': None}
        version = 'tosca_aria_yaml_{0}'.format(version or '1_0')

        node_templates = {}
        for node, contained_in in nodes.iteritems():
            node_template = {'type': 'type'}
            if contained_in:
                node_template['relationships'] = [
                    {'type': 'tosca.relationships.HostedOn',
                     'target': contained_in}
                ]
            node_templates[node] = node_template

        blueprint_groups = dict(
            (group, item if isinstance(item, dict) else {'members': item})
            for group, item in groups.iteritems())

        blueprint = {
            'tosca_definitions_version': version,
            'node_types': {'type': {}},
            'relationships': {'tosca.relationships.HostedOn': {}},
            'node_templates': node_templates,
            'groups': blueprint_groups,
        }

        if policies:
            blueprint['policies'] = policies
        if policy_types is not None:
            blueprint['policy_types'] = policy_types

        self.clear()
        self.template += safe_dump(blueprint)

    def from_blueprint_dict(self, blueprint):
        self.clear()
        self.template += safe_dump(blueprint)

    def clear(self):
        self.template = ''

    def version_section(self, version, raw=False, support=True):
        version_structure = supported_versions.create_version_structure(
            '_'.join((BASE_VERSION_PROFILE, version.replace('.', '_'))))
        version_str = (
            '\ntosca_definitions_version: {0}\n'.format(
                version_structure.name))
        if support:
            add_version_to_database(BASE_VERSION_PROFILE, version_structure)
        if raw:
            return version_str
        self.template += version_str

    def node_type_section(self, default='"default"'):
        self.template += (
            '\nnode_types:\n'
            '    test_type:\n'
            '        properties:\n'
            '            key:\n'
            '                default: {0}\n'
        ).format(default)

    def node_template_section(self):
        self.template += self.BASIC_NODE_TEMPLATES_SECTION

    def data_types_section(
            self,
            properties_first='{}',
            properties_second='{}',
            extras=''):

        self.template += (
            '\ndata_types:\n'
            '    pair_type:\n'
            '        properties:\n'
            '            first: {properties_first}\n'
            '            second: {properties_second}\n'
            '{extras}\n'
            .format(properties_first=properties_first,
                    properties_second=properties_second,
                    extras=extras)
        )

    def plugin_section(self):
        self.template += self.BASIC_PLUGIN

    def input_section(self):
        self.template += (
            '\ninputs:\n'
            '    test_input:\n'
            '        type: string\n'
            '        default: test_input_default_value\n'
        )

    def output_section(self):
        self.template += (
            '\noutputs:\n'
            '    test_output:\n'
            '        value: test_output_value\n'
        )


def get_node_by_name(plan, name):
    return [x for x in plan.node_templates if x['name'] == name][0]


def get_nodes_by_names(plan, names):
    return [
        node
        for node in plan.node_templates
        for name in names
        if node['id'] == name
    ]


def op_struct(
        plugin_name,
        mapping,
        inputs=None,
        executor='local',
        max_retries=None,
        retry_interval=None):
    return {
        'plugin': plugin_name,
        'operation': mapping,
        'inputs': inputs or {},
        'executor': executor,
        'has_intrinsic_functions': False,
        'max_retries': max_retries,
        'retry_interval': retry_interval,
    }

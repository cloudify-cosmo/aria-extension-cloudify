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
from yaml import safe_dump
from itertools import imap
from tempfile import mkdtemp
from testtools import TestCase

from aria.parser import Parser
from aria.parser.dsl_supported_versions import (
    supported_versions,
    BASE_VERSION_PROFILE,
    add_version_to_database,
)
from aria.exceptions import DSLParsingException
from aria.deployment import prepare_deployment_plan


class TempDirectoryTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super(TempDirectoryTestCase, self).__init__(*args, **kwargs)
        self.temp_directory = None
        self._path_to_uri = 'file://{0}'.format

    def setUp(self):
        self.temp_directory = mkdtemp(prefix=self.__class__.__name__)
        super(TempDirectoryTestCase, self).setUp()

    def tearDown(self):
        rmtree(self.temp_directory, ignore_errors=True)
        super(TempDirectoryTestCase, self).tearDown()

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
    def __init__(self, *args, **kwargs):
        super(ParserTestCase, self).__init__(*args, **kwargs)
        self.template = None

    def setUp(self):
        self.template = Template()
        super(ParserTestCase, self).setUp()

    def tearDown(self):
        self.template = None
        super(ParserTestCase, self).tearDown()

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

    def from_blouprint_dict(self, blueprint):
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
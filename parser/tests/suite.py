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

import os
from uuid import uuid4
from shutil import rmtree
from aria.utils import yaml_dumps
from itertools import imap
from tempfile import mkdtemp

from testtools import TestCase

from dsl_parser.parser import parse, parse_from_path


PARSING_ISSUES_TITLE = 'parse failed with issues: \n\t'


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

        return (
            '\nimports:\n  - {0}'.format(
                '\n  - '.join(imap(import_creator, contents))))


class ParserTestCase(TestCase):
    template = None

    def setUp(self):
        self.template = Template()
        super(ParserTestCase, self).setUp()

    def parse(
            self,
            resources_base_url=None,
            template_inputs=None,
            validate_version=True):
        if template_inputs:
            template = str(self.template) % template_inputs
        else:
            template = str(self.template)
        context = parse(
            dsl_string=template,
            resources_base_url=resources_base_url,
            validate_version=validate_version)
        self._validate_parse_no_issues(context)

        return context.modeling.classic_deployment_plan

    def parse_from_uri(self, uri):
        context = parse_from_path(uri)
        self._validate_parse_no_issues(context)
        return context.modeling.classic_deployment_plan

    def _validate_parse_no_issues(self, context):
        if not context.validation.has_issues:
            return
        msg = '{title}{messages}'.format(
            title=PARSING_ISSUES_TITLE,
            messages='\n\t'.join(
                issue.message for issue in context.validation.issues))
        raise CloudifyParserError(msg)

    def assert_parser_issue_messages(self,
                                     issue_messages,
                                     parse_from_path=False,
                                     parsing_arguments=None):
        parsing_method = self.parse_from_uri if parse_from_path else self.parse
        parsing_arguments = parsing_arguments or []

        ex = self.assertRaises(CloudifyParserError,
                               parsing_method,
                               *parsing_arguments)

        expected_error_message = '{title}{messages}'.format(
            title=PARSING_ISSUES_TITLE,
            messages='\n\t'.join(msg for msg in issue_messages))

        self.assertEqual(expected_error_message, ex.message)




class Template(object):
    BASIC_NODE_TEMPLATES_SECTION = (
        '\n'
        'node_templates:\n'
        '  test_node:\n'
        '    type: test_type\n'
        '    properties:\n'
        '      key: "val"\n'
    )

    BASIC_PLUGIN = (
        '\nplugins:\n'
        '  test_plugin:\n'
        '    executor: central_deployment_agent\n'
        '    source: dummy\n'
    )

    BASIC_TYPE = (
        '\n'
        'node_types:\n'
        '  test_type:\n'
        '    interfaces:\n'
        '      test_interface1:\n'
        '        install:\n'
        '          implementation: test_plugin.install\n'
        '          inputs: {}\n'
        '        terminate:\n'
        '          implementation: test_plugin.terminate\n'
        '          inputs: {}\n'
        '    properties:\n'
        '      install_agent:\n'
        '        default: "false"\n'
        '      key: {}\n'
    )

    PLUGIN_WITH_INSTALL_ARGS = (
        '\n'
        'plugins:\n'
        '  test_plugin:\n'
        '    executor: central_deployment_agent\n'
        '    source: dummy\n'
        '    install_arguments: -r requirements.txt\n'
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
        version = 'cloudify_dsl_{0}'.format(version or '1_3')

        node_templates = {}
        for node, contained_in in nodes.iteritems():
            node_template = {'type': 'type'}
            if contained_in:
                node_template['relationships'] = [
                    {'type': 'cloudify.relationships.contained_in',
                     'target': contained_in}
                ]
            node_templates[node] = node_template

        blueprint_groups = dict(
            (group, item if isinstance(item, dict) else {'members': item})
            for group, item in groups.iteritems())

        blueprint = {
            'tosca_definitions_version': version,
            'node_types': {'type': {}},
            'relationships': {'cloudify.relationships.contained_in': {}},
            'node_templates': node_templates,
            'groups': blueprint_groups,
        }

        if policies:
            blueprint['policies'] = policies
        if policy_types is not None:
            blueprint['policy_types'] = policy_types

        self.clear()
        self.template += yaml_dumps(blueprint)

    def from_blueprint_dict(self, blueprint):
        self.clear()
        self.template += yaml_dumps(blueprint)

    def clear(self):
        self.template = ''

    def version_section(self, profile, version, raw=False):
        version_section = (
            '\n'
            'tosca_definitions_version: {0}_{1}\n'
            '\n'
        ).format(profile, version.replace('.', '_'))

        if raw:
            return version_section
        self.template += version_section

    def node_type_section(self, default='"default"'):
        self.template += (
            '\n'
            'node_types:\n'
            '  test_type:\n'
            '    properties:\n'
            '      key:\n'
            '        default: {0}\n'
        ).format(default)

    def node_template_section(self):
        self.template += self.BASIC_NODE_TEMPLATES_SECTION

    def data_types_section(
            self,
            properties_first='{}',
            properties_second='{}',
            extras=''):

        self.template += (
            '\n'
            'data_types:\n'
            '  pair_type:\n'
            '    properties:\n'
            '      first: {properties_first}\n'
            '      second: {properties_second}\n'
            '{extras}\n'
            .format(properties_first=properties_first,
                    properties_second=properties_second,
                    extras=extras)
        )

    def plugin_section(self):
        self.template += self.BASIC_PLUGIN

    def input_section(self):
        self.template += (
            '\n'
            'inputs:\n'
            '  test_input:\n'
            '    type: string\n'
            '    default: test_input_default_value\n'
        )

    def output_section(self):
        self.template += (
            '\n'
            'outputs:\n'
            '  test_output:\n'
            '    value: test_output_value\n'
        )

class CloudifyParserError(Exception):
    pass

def op_struct(
        plugin_name,
        mapping,
        inputs=None,
        executor=None,
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


def get_node_by_name(plan, name):
    return get_nodes_by_names(plan, [name])[0]


def get_nodes_by_names(plan, names):
    return [
        node
        # for node in plan.node_templates
        for node in plan['nodes']
        for name in names
        if node['id'] == name
    ]

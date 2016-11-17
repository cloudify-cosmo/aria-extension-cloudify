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

from .templates import ServiceTemplate
from .assignments import InterfaceAssignment
from .functions import GetInput, GetProperty, GetAttribute
from .modeling import create_service_model
from aria.validation import Issue
from aria.presentation import Presenter
from aria.utils import EMPTY_READ_ONLY_LIST, cachedmethod

class CloudifyPresenter1_0(Presenter):
    """
    ARIA presenter for the `Cloudify DSL v1.0 specification <http://getcloudify.org/guide/3.1/dsl-spec-general.html>`__.

    Supported :code:`tosca_definitions_version` values:
    
    * :code:`cloudify_dsl_1_0`
    """

    DSL_VERSIONS = ('cloudify_dsl_1_0',)
    ALLOWED_IMPORTED_DSL_VERSIONS = ('cloudify_dsl_1_0',)
    INTERFACE_ASSIGNMENT_CLASS = InterfaceAssignment
    
    @property
    @cachedmethod
    def service_template(self):
        return ServiceTemplate(raw=self._raw)
    
    @property
    @cachedmethod
    def functions(self):
        return {
            'get_input': GetInput,
            'get_property': GetProperty,
            'get_attribute': GetAttribute}

    # Presentation

    def _dump(self, context):
        self.service_template._dump(context)

    def _validate(self, context):
        self.service_template._validate(context)

    # Presenter

    def _get_import_locations(self, context):
        imports = self._get('service_template', 'imports')
        return imports if imports is not None else EMPTY_READ_ONLY_LIST

    def _validate_import(self, context, presentation):
        r = True
        if not super(CloudifyPresenter1_0, self)._validate_import(context, presentation):
            r = False
        if presentation._get('service_template', 'inputs') is not None:
            context.validation.report('import has forbidden "inputs" section', locator=presentation._get_child_locator('inputs'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation._get('service_template', 'outputs') is not None:
            context.validation.report('import has forbidden "outputs" section', locator=presentation._get_child_locator('outputs'), level=Issue.BETWEEN_TYPES)
            r = False
        if presentation._get('service_template', 'node_templates') is not None:
            context.validation.report('import has forbidden "node_templates" section', locator=presentation._get_child_locator('node_templates'), level=Issue.BETWEEN_TYPES)
            r = False
            
        # Note: The documentation specifies that importing "groups" is also not allowed:
        #
        # http://getcloudify.org/guide/3.1/dsl-spec-imports.html
        #
        # However, the documentation is *wrong*. Importing "groups" has always been allowed
        # in the parser code.
        #
        # This documentation error continued all the way to DSL 1.3:
        #
        # http://docs.getcloudify.org/3.4.0/blueprints/spec-imports/

        return r

    @cachedmethod
    def _get_service_model(self, context):
        return create_service_model(context)

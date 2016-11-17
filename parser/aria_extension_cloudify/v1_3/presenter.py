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
from ..v1_2 import CloudifyPresenter1_2
from aria.presentation import Presenter
from aria.utils import cachedmethod

class CloudifyPresenter1_3(CloudifyPresenter1_2):
    """
    ARIA presenter for the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/overview/>`__.
    
    Supported :code:`tosca_definitions_version` values:
    
    * :code:`cloudify_dsl_1_3`

    Changes over v1.2:

    * `Policies <http://docs.getcloudify.org/3.4.0/blueprints/spec-policies/>`__.
    * Imports no longer forbid `inputs`, `outputs', and `node_templates`.
    * Addition of `capabilities` to `node templates <http://docs.getcloudify.org/3.4.0/blueprints/spec-node-templates/>`__.
    * Deprecate `instances` in `node templates <http://docs.getcloudify.org/3.4.0/blueprints/spec-node-templates/>`__.
    """

    DSL_VERSIONS = ('cloudify_dsl_1_3',)
    ALLOWED_IMPORTED_DSL_VERSIONS = ('cloudify_dsl_1_3', 'cloudify_dsl_1_2', 'cloudify_dsl_1_1', 'cloudify_dsl_1_0')

    @property
    @cachedmethod
    def service_template(self):
        return ServiceTemplate(raw=self._raw)

    # Presenter

    def _validate_import(self, context, presentation):
        r = True
        if not Presenter._validate_import(self, context, presentation):
            r = False
        return r

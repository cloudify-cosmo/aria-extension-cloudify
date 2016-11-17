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
from ..v1_1 import CloudifyPresenter1_1
from aria.utils import cachedmethod

class CloudifyPresenter1_2(CloudifyPresenter1_1):
    """
    ARIA presenter for the `Cloudify DSL v1.2 specification <http://docs.getcloudify.org/3.3.1/blueprints/overview/>`__.
    
    Supported :code:`tosca_definitions_version` values:
    
    * :code:`cloudify_dsl_1_2`

    Changes over v1.1:
    
    * `Data types <http://docs.getcloudify.org/3.3.1/blueprints/spec-data-types/>`__.
    * `Upload resources <http://docs.getcloudify.org/3.3.1/blueprints/spec-upload-resources/>`__.
    * Addition of `dsl_definitions` to `blueprint <http://docs.getcloudify.org/3.3.1/blueprints/spec-dsl-definitions/>`__.
    * Addition of `package_name`, `package_version`, `supported_platform`, `distribution`, `distribution_version`, and `distribution_release` to `plugin definitions <http://docs.getcloudify.org/3.3.1/blueprints/spec-plugins/>`__.
    * Addition of `description` to blueprint.
    * Addition of `required` to property definitions.
    """

    DSL_VERSIONS = ('cloudify_dsl_1_2',)
    ALLOWED_IMPORTED_DSL_VERSIONS = ('cloudify_dsl_1_2', 'cloudify_dsl_1_1', 'cloudify_dsl_1_0')

    @property
    @cachedmethod
    def service_template(self):
        return ServiceTemplate(raw=self._raw)

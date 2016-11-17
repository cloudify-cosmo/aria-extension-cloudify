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

from .modeling.plugins import validate_plugin
from ..v1_1 import Plugin as Plugin1_1
from aria import dsl_specification
from aria.presentation import Presentation, has_fields, primitive_field, object_list_field

@has_fields
@dsl_specification('plugins', 'cloudify-1.2')
@dsl_specification('plugins', 'cloudify-1.3')
class Plugin(Plugin1_1):
    @primitive_field(str)
    def package_name(self):
        """
        Managed plugin package name. (Supported since: :code:`cloudify_dsl_1_2`) If install is false, pacakge_name is redundant. If install is true, package_name (or source) is mandatory.
        
        :rtype: str
        """

    @primitive_field(str)
    def package_version(self):
        """
        Managed plugin package version. (Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: :class:`Version`
        """

    @primitive_field(str)
    def supported_platform(self):
        """
        Managed plugin supported platform (e.g. :code:`linux_x86_64`). (Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: str
        """

    @primitive_field(str)
    def distribution(self):
        """
        Managed plugin distribution. (Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: str
        """

    @primitive_field(str)
    def distribution_version(self):
        """
        Managed plugin distribution version. (Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: :class:`Version`
        """

    @primitive_field(str)
    def distribution_release(self):
        """
        Managed plugin distribution release. (Supported since: :code:`cloudify_dsl_1_2`)
        
        :rtype: str
        """

    def _validate(self, context):
        Presentation._validate(self, context)
        validate_plugin(context, self)

@has_fields
class PluginResource(Presentation):
    @primitive_field(str, required=True)
    def source_path(self):
        """
        The source path for the dsl resource.
        
        :rtype: str
        """
    
    @primitive_field(str, required=True)
    def destination_path(self):
        """
        A relative destination path for the resource (relative to the file server home dir).
        
        :rtype: str
        """

@has_fields
@dsl_specification('upload-resources', 'cloudify-1.2')
@dsl_specification('upload-resources', 'cloudify-1.3')
class UploadResources(Presentation):
    """
    Cloudify provides you with a simple way for uploading resources to the manager.

    See the `Cloudify DSL v1.3 specification <http://docs.getcloudify.org/3.4.0/blueprints/spec-upload-resources/>`__.
    """
    
    @object_list_field(PluginResource)
    def plugin_resources(self):
        """
        A list of `wgn <https://github.com/cloudify-cosmo/wagon>`__ plugins (URLs or local paths) to be uploaded to the manager.
        
        :rtype: list of :class:`PluginResource`
        """

    @primitive_field()
    def dsl_resources(self):
        """
        A list of dictionaries each comprises a `source_path` and `destination_path` for each `dsl_resource`.
        """

    @primitive_field()
    def parameters(self):
        """
        Describes the different parameters for the upload of resources.
        """

    @primitive_field(int)
    def fetch_timeout(self):
        """
        (3.3.1 feature) Max idle time (in seconds) while fetching any resource. Note that the timeout refers to an idle connection, and not the entire download process.
        
        :rtype: int
        """

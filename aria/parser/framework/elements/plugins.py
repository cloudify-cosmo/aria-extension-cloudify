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

from ...exceptions import DSLParsingLogicException
from ...dsl_supported_versions import supported_versions
from .version import ToscaDefinitionsVersion
from . import Element, Leaf, Dict, DictElement


class PluginSource(Element):
    schema = Leaf(type=str)


class PluginInstall(Element):
    schema = Leaf(type=bool)

    def parse(self):
        return self.initial_value if self.initial_value is not None else True


class PluginVersionValidatedElement(Element):
    schema = Leaf(type=str)
    requires = {
        ToscaDefinitionsVersion: ['version'],
        'inputs': ['validate_version'],
    }

    def validate_version(self, version):
        if not self.supported_version:
            raise RuntimeError('Illegal state, please specify min_version')
        super(PluginVersionValidatedElement, self).validate_version(version)


class PluginInstallArguments(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginPackageName(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginPackageVersion(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginSupportedPlatform(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginDistribution(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginDistributionVersion(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class PluginDistributionRelease(PluginVersionValidatedElement):
    supported_version = supported_versions.base_version


class Plugin(DictElement):
    schema = {
        'source': PluginSource,
        'install': PluginInstall,
        'install_arguments': PluginInstallArguments,
        'package_name': PluginPackageName,
        'package_version': PluginPackageVersion,
        'supported_platform': PluginSupportedPlatform,
        'distribution': PluginDistribution,
        'distribution_version': PluginDistributionVersion,
        'distribution_release': PluginDistributionRelease,
    }

    def validate(self, **kwargs):
        if not self.child(PluginInstall).value:
            return
        if (self.child(PluginSource).value or
                self.child(PluginPackageName).value):
            return
        raise DSLParsingLogicException(
            50,
            "Plugin '{0}' needs to be installed, "
            "but does not declare a source or package_name property"
            .format(self.name))

    def parse(self):
        result = super(Plugin, self).parse()
        result['name'] = self.name
        return result


class Plugins(DictElement):
    schema = Dict(type=Plugin)

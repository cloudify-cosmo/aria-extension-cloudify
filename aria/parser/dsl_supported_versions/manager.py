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

from itertools import imap
from collections import namedtuple

from ..exceptions import DSLParsingLogicException

VERSION = 'tosca_definitions_version'
BASE_VERSION_PROFILE = 'tosca_aria_yaml'


class VersionNumber(namedtuple('VersionNumber', 'major, minor, micro')):
    def __new__(cls, major, minor, micro=0):
        return super(VersionNumber, cls).__new__(cls, major, minor, micro)

    def __repr__(self):
        return (
            '{cls.__name__}'
            '(major={self.major}, minor={self.minor}, micro={self.micro})'
            .format(cls=self.__class__, self=self))


class VersionStructure(namedtuple('VersionStructure', 'profile, number')):
    def __repr__(self):
        return (
            '{cls.__name__}(profile={self.profile}, number={self.number!r})'
            .format(cls=self.__class__, self=self))

    @property
    def name(self):
        return (
            '{self.profile}_{self.number.major}_'
            '{self.number.minor}_{self.number.micro}'.format(self=self))


class SupportedVersions(object):
    def __init__(self, database):
        self.database = database

    def __contains__(self, version):
        return any(imap(
            lambda supported_version: supported_version == version,
            self.versions()))

    @property
    def base_version(self):
        return next(iter(self.database[BASE_VERSION_PROFILE]))

    def versions(self):
        for version_structures in self.database.itervalues():
            for version_structure in version_structures:
                yield version_structure

    def create_version_structure(self, version_name):
        if not version_name:
            raise DSLParsingLogicException(
                71, '{0} is missing or empty'.format(VERSION))

        if not isinstance(version_name, basestring):
            raise DSLParsingLogicException(
                72, 'Invalid {0}: {1} is not a string'.format(
                    VERSION, version_name))

        for prefix in self.database.iterkeys():
            if version_name.startswith(prefix):
                short_dsl_version = version_name[len(prefix) + 1:]
                break
        else:
            raise DSLParsingLogicException(
                73, "Invalid {0}: '{1}', expected a value following "
                    "this format: '{2}'".format(
                        VERSION, version_name, self.base_version.name))

        if '_' not in short_dsl_version:
            raise DSLParsingLogicException(
                73, "Invalid {0}: '{1}', "
                    "expected a value following this format: '{2}'".format(
                        VERSION, version_name, self.base_version.name))

        version_parts = short_dsl_version.split('_')
        if len(version_parts) == 2:
            major, minor = version_parts
            micro = '0'
        else:
            major, minor, micro = version_parts

        if not major.isdigit():
            raise DSLParsingLogicException(
                74, "Invalid {0}: '{1}', major version is '{2}' "
                    "while expected to be a number".format(
                        VERSION, version_name, major))

        if not minor.isdigit():
            raise DSLParsingLogicException(
                75, "Invalid {0}: '{1}', minor version is '{2}' "
                    "while expected to be a number".format(
                        VERSION, version_name, minor))

        if not micro.isdigit():
            raise DSLParsingLogicException(
                76, "Invalid {0}: '{1}', micro version is '{2}' "
                    "while expected to be a number".format(
                        VERSION, version_name, micro))

        return VersionStructure(
            profile=prefix,
            number=VersionNumber(int(major), int(minor), int(micro)))

    def validate_dsl_version(self, version_structure):
        if version_structure not in self:
            raise DSLParsingLogicException(
                29,
                'Unexpected tosca_definitions_version {0!r}; Currently '
                'supported versions are: {1}'
                .format(version_structure, list(self.versions())))

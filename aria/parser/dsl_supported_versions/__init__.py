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

from .database import database
from .manager import (
    VERSION,
    BASE_VERSION_PROFILE,
    VersionNumber,
    VersionStructure,
    SupportedVersions,
)

supported_versions = SupportedVersions(database)  # pylint: disable=invalid-name


def add_version_to_database(profile, version_structure):
    database[profile].add(version_structure)


def parse_dsl_version(version_name):
    version_structure = supported_versions.create_version_structure(version_name)
    supported_versions.validate_dsl_version(version_structure)
    return version_structure


def process_dsl_version(dsl_version):
    version_structure = parse_dsl_version(dsl_version)
    return {
        'raw': version_structure.name,
        'definitions_name': version_structure.profile,
        'definitions_version': version_structure,
    }

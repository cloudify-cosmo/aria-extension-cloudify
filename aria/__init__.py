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

"""
aria Package
Path: aria

Methods:
    * __version__ - Aria Package Version.
    * tosca_templates - Use the parser.parse method to validate tosca_templates.
    * parser - aria.parser sub-package TOSCA parser and validation.
    * deployment - aria.deployment sub-package convert plan,
                   from parser to a deployment plan.
"""

from .VERSION import version as __version__
from .storage.drivers import ResourceDriver, ModelDriver, FileSystemModelDriver, FileSystemResourceDriver
from .storage import ModelStorage, ResourceStorage, models
from . import parser

__all__ = (
    '__version__',
    'parser',
    'validate_template',
    'workflow',
    'operation',
)

validate_template = parser.parse  # pylint: disable=C0103


_model_storages = {}
_resource_storages = {}


def application_model_storage(driver):
    assert isinstance(driver, ModelDriver)
    global _model_storages
    if driver not in _model_storages:
        _model_storages[driver] = ModelStorage(
            driver, models=[
                models.Node,
                models.NodeInstance,
                models.Plugin,
                models.Blueprint,
                models.Snapshot,
                models.Deployment,
                models.DeploymentUpdate,
                models.DeploymentModification,
                models.Execution,
                models.ProviderContext,
                models.Operation,
            ])
    return _model_storages[driver]


def application_resource_storage(driver):
    assert isinstance(driver, ResourceDriver)
    global _resource_storages
    if driver not in _resource_storages:
        _resource_storages[driver] = ResourceStorage(
            driver,
            resources=[
                'blueprint',
                'deployment',
                'plugin',
                'snapshot',
            ])
    return _resource_storages[driver]

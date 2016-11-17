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

from .presenter import CloudifyPresenter1_3
from .templates import NodeTemplate, GroupTemplate, PolicyTemplate, ServiceTemplate
from .assignments import CapabilityAssignment

MODULES = (
    'modeling',)

__all__ = (
    'MODULES',
    'CloudifyPresenter1_3',
    'NodeTemplate',
    'GroupTemplate',
    'PolicyTemplate',
    'ServiceTemplate',
    'CapabilityAssignment')

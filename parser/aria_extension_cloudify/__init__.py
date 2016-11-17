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

from .v1_0 import CloudifyPresenter1_0
from .v1_1 import CloudifyPresenter1_1
from .v1_2 import CloudifyPresenter1_2
from .v1_3 import CloudifyPresenter1_3
from .classic_modeling import ClassicDeploymentPlan
from aria import DSL_SPECIFICATION_PACKAGES
from aria.presentation import PRESENTER_CLASSES

def install_aria_extension():
    global PRESENTER_CLASSES
    PRESENTER_CLASSES += (CloudifyPresenter1_0, CloudifyPresenter1_1, CloudifyPresenter1_2, CloudifyPresenter1_3)
    
    # DSL specification
    DSL_SPECIFICATION_PACKAGES.append('aria_extension_cloudify')

MODULES = (
    'classic_modeling',
    'v1_0',
    'v1_1',
    'v1_2',
    'v1_3')

__all__ = (
    'MODULES',
    'install_aria_extension',
    'ClassicDeploymentPlan')

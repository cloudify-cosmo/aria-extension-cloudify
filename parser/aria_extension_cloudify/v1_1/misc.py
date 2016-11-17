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

from ..v1_0 import Plugin as Plugin1_0
from aria import dsl_specification
from aria.presentation import has_fields, primitive_field 

@has_fields
@dsl_specification('plugins', 'cloudify-1.1')
class Plugin(Plugin1_0):
    @primitive_field(str)
    def install_arguments(self):
        """
        Optional arguments passed to the :code:`pip install` command created for the plugin installation.
        
        :rtype: str        
        """

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

from aria.validation import Issue

def validate_plugin(context, presentation):
    """
    Makes sure the plugin has :code:`source` or :code:`package_name` set if :code:`install` is true.
    """
    
    if presentation.install:
        if (presentation.source is None) and (presentation.package_name is None):
            context.validation.report('plugin "%s" is set to install but does not have "source" or "package_name"' % presentation._name, locator=presentation._locator, level=Issue.BETWEEN_FIELDS)

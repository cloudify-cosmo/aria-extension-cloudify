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

from aria.modeling import Parameter, Function

def has_intrinsic_functions(context, value):
    """
    Checks if the value contains intrinsic functions, recursively.
    """
    
    if isinstance(value, Parameter):
        value = value.value

    if isinstance(value, Function):
        return True
    elif isinstance(value, dict):
        for v in value.itervalues():
            if has_intrinsic_functions(context, v):
                return True
    elif isinstance(value, list):
        for v in value:
            if has_intrinsic_functions(context, v):
                return True
    return False


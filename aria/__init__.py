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

from . import parser
from . import deployment
from .version import __version__

__all__ = [
    '__version__',
    'parser',
    'deployment',
    'validate_template',
]

validate_template = parser.parse  # pylint: disable=C0103

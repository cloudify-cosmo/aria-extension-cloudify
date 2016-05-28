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

from aria.parser.framework.parser import parse
from aria.parser.framework.elements import Element
from aria.parser.framework.elements.data_types import DataTypes
from aria.parser.framework.elements.version import ToscaDefinitionsVersion


def validate(obj, element_cls):
    schema = {
        'tosca_definitions_version': ToscaDefinitionsVersion,
        'test': element_cls,
        'data_types': DataTypes,
    }
    parse(
        value={'tosca_definitions_version': 'tosca_aria_yaml_1_0', 'test': obj},
        element_cls=type('TestElement', (Element,), {'schema': schema}),
        inputs={'validate_version': True},
        strict=True)

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

from ...exceptions import DSLParsingLogicException, DSLParsingFormatException
from .node_templates import NodeTemplates
from . import DictElement, Element, Leaf, List, Dict


class GroupMember(Element):
    schema = Leaf(type=basestring)
    requires = {NodeTemplates: ['node_template_names']}

    def validate(self, node_template_names):
        if self.initial_value not in node_template_names:
            raise DSLParsingLogicException(
                40,
                "Member '{0}' of group '{1}' does not "
                "match any defined node".format(
                    self.initial_value,
                    self.ancestor(Group).name))


class GroupMembers(Element):
    required = True
    schema = List(type=GroupMember)

    def validate(self, **kwargs):
        if len(self.children()) < 1:
            raise DSLParsingFormatException(
                1, "At least one member should be specified")

    def parse(self):
        # ensure uniqueness
        return list(set([c.value for c in self.children()]))


class Group(DictElement):
    schema = {
        'members': GroupMembers,
    }


class Groups(DictElement):
    schema = Dict(type=Group)

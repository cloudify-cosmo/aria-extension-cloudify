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

from ...interfaces import merge_relationship_type_interfaces
from ... import constants, utils
from .. import Requirement, Value
from .plugins import Plugins
from .types import Type, Types, RelationshipDerivedFrom, derived_from_predicate
from .data_types import SchemaWithInitialDefault, DataTypes
from .operation import NodeTypeInterfaces, process_interface_operations
from . import Dict, Element


class RelationshipMapping(Element):
    types = {
        'depens_on_relationship_type': 'tosca.relationships.DependsOn',
        # 'contained_in_relationship_type': 'tosca.relationships.HostedOn',
        'contained_in_relationship_type': 'cloudify.relationships.contained_in',
        'contained_to_relationship_type': 'tosca.relationships.ConnectsTo',
        'group_contained_in_relationship_type': '__group_contained_in__',
        'connection_type': 'connection_type',
    }

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        pass

    def __getattr__(self, item):
        try:
            if self.extend:
                return self.extend.types[item]
            return self.types[item]
        except KeyError:
            return super(RelationshipMapping, self).__getattribute__(item)

    def __iter__(self):
        for relationship_type in self.types:
            yield getattr(self, relationship_type)


class Relationship(Type):
    schema = {
        'derived_from': RelationshipDerivedFrom,
        'properties': SchemaWithInitialDefault,
        'source_interfaces': NodeTypeInterfaces,
        'target_interfaces': NodeTypeInterfaces,
    }
    requires = {
        'inputs': [Requirement('resource_base', required=False)],
        Plugins: [Value('plugins')],
        'self': [Value('super_type',
                       predicate=derived_from_predicate,
                       required=False)],
        DataTypes: [Value('data_types')],
    }

    def parse(self, super_type, plugins, resource_base, data_types, **_):
        relationship_type = self.build_dict_result()
        if not relationship_type.get('derived_from'):
            relationship_type.pop('derived_from', None)
        relationship_type_name = self.name

        if super_type:
            relationship_type[constants.PROPERTIES] = utils.merge_schemas(
                overridden_schema=super_type.get('properties', {}),
                overriding_schema=relationship_type.get('properties', {}),
                data_types=data_types)
            for interfaces in [constants.SOURCE_INTERFACES,
                               constants.TARGET_INTERFACES]:
                relationship_type[interfaces] = (
                    merge_relationship_type_interfaces(
                        overriding_interfaces=relationship_type[interfaces],
                        overridden_interfaces=super_type[interfaces]))

        _validate_relationship_fields(
            rel_obj=relationship_type,
            plugins=plugins,
            rel_name=relationship_type_name,
            resource_base=resource_base)
        relationship_type['name'] = relationship_type_name
        relationship_type[
            constants.TYPE_HIERARCHY] = self.create_type_hierarchy(super_type)
        self.fix_properties(relationship_type)
        return relationship_type


class Relationships(Types):
    schema = Dict(obj_type=Relationship)


def _validate_relationship_fields(rel_obj, plugins, rel_name, resource_base):
    for interfaces in [constants.SOURCE_INTERFACES,
                       constants.TARGET_INTERFACES]:
        for interface in rel_obj[interfaces].itervalues():
            process_interface_operations(
                interface=interface,
                plugins=plugins,
                error_code=19,
                partial_error_message="Relationship '{0}'".format(rel_name),
                resource_base=resource_base)

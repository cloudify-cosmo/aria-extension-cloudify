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

CONTAINED_IN_RELATIONSHIP_NAME = 'cloudify.relationships.contained_in'

def is_contained_in(context, relationship_or_relationship_template):
    """
    Whether we are a contained-in relationship or relationship template.
    """

    if relationship_or_relationship_template is None:
        return False
    return context.modeling.relationship_types.is_descendant(CONTAINED_IN_RELATIONSHIP_NAME, relationship_or_relationship_template.type_name)

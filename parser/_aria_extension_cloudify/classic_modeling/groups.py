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

from .relationships import is_contained_in
from .policies import SCALING_POLICY_NAME

def find_groups(context, node):
    """
    Returns a list of all groups that contain the node.
    """
    
    groups = []
    for group in context.modeling.instance.groups.itervalues():
        if node.id in group.member_node_ids:
            groups.append(group)
    return groups

def iter_scaling_groups(context):
    """
    Iterates the groups referred to by scaling policies.
    """
    
    for policy_template in context.modeling.model.policy_templates.itervalues():
        if policy_template.type_name == SCALING_POLICY_NAME:
            for group_template_name in policy_template.target_group_template_names:
                group_template = context.modeling.model.group_templates[group_template_name]
                yield group_template_name, group_template, policy_template

def prune_redundant_members(context, node_template_names, group_template_names=set()):
    """
    Makes sure the set of group members is the most minimal by removing redundant members.
    The final result will produce exactly the same list of nodes as the original.
    """
    
    # Remove groups that are implied by other groups
    redundant_group_template_names = set()
    for group_template_name in group_template_names:
        implied = False
        for other_group_template_name in group_template_names:
            if other_group_template_name == group_template_name:
                continue
            if _is_group_template_implied_by_group_template(context, group_template_name, other_group_template_name):
                implied = True
                break
        if implied:
            redundant_group_template_names.add(group_template_name)
    group_template_names -= redundant_group_template_names

    # Remove nodes that are implied by other nodes or groups
    redundant_node_template_names = set()
    for node_template_name in node_template_names:
        implied = False
        for other_node_template_name in node_template_names:
            if other_node_template_name == node_template_name:
                continue
            if _is_node_template_implied_by_node_template(context, node_template_name, other_node_template_name):
                implied = True
                break
        if not implied:
            for group_template_name in group_template_names:
                if _is_node_template_implied_by_group_template(context, node_template_name, group_template_name):
                    implied = True
                    break
        if implied:
            redundant_node_template_names.add(node_template_name)
    node_template_names -= redundant_node_template_names

    # Remove groups that don't add any new nodes
    redundant_group_template_names = set()
    for group_template_name in group_template_names:
        # Our nodes
        our_implied_node_template_names = _get_node_templates_implied_by_group_template(context, group_template_name)
        prune_redundant_members(context, our_implied_node_template_names)
        
        # The other nodes
        other_implied_node_template_names = set(node_template_names)
        for other_group_template_name in group_template_names:
            if (other_group_template_name == group_template_name) or (other_group_template_name in redundant_group_template_names): 
                continue
            other_implied_node_template_names |= _get_node_templates_implied_by_group_template(context, other_group_template_name)
        
        if other_implied_node_template_names and our_implied_node_template_names <= other_implied_node_template_names:
            redundant_group_template_names.add(group_template_name)
    group_template_names -= redundant_group_template_names

#
# Utils
#

def _is_node_template_implied_by_node_template(context, node_template_name, other_node_template_name):
    node_template = context.modeling.model.node_templates.get(node_template_name)
    for requirement in node_template.requirements:
        if is_contained_in(context, requirement.relationship_template):
            if requirement.target_node_template_name == other_node_template_name:
                return True
            if _is_node_template_implied_by_node_template(context, requirement.target_node_template_name, other_node_template_name):
                return True
    return False

def _is_node_template_implied_by_group_template(context, node_template_name, group_template_name):
    group_template = context.modeling.model.group_templates.get(group_template_name)
    for member_node_template_name in group_template.member_node_template_names:
        if node_template_name == member_node_template_name:
            return True
        if _is_node_template_implied_by_node_template(context, node_template_name, member_node_template_name):
            return True
        for member_group_template_name in group_template.member_group_template_names:
            if _is_node_template_implied_by_group_template(context, node_template_name, member_group_template_name):
                return True
    return False

def _is_group_template_implied_by_group_template(context, group_template_name, other_group_template_name):
    other_group_template = context.modeling.model.group_templates.get(other_group_template_name)
    for member_group_template_name in other_group_template.member_group_template_names:
        if member_group_template_name == group_template_name:
            return True
        elif _is_group_template_implied_by_group_template(context, group_template_name, member_group_template_name):
            return True
    return False

def _get_node_templates_implied_by_node_template(context, node_template_name):
    node_template_names = set()
    node_template_names.add(node_template_name)
    node_template = context.modeling.model.node_templates.get(node_template_name)
    for requirement in node_template.requirements:
        if is_contained_in(context, requirement.relationship_template):
            node_template_names |= _get_node_templates_implied_by_node_template(context, requirement.target_node_template_name)
    return node_template_names

def _get_node_templates_implied_by_group_template(context, group_template_name):
    node_template_names = set()
    group_template = context.modeling.model.group_templates.get(group_template_name)
    for member_node_template_name in group_template.member_node_template_names:
        node_template_names |= _get_node_templates_implied_by_node_template(context, member_node_template_name)
    for member_group_template_name in group_template.member_group_template_names:
        node_template_names |= _get_node_templates_implied_by_group_template(context, member_group_template_name)
    return node_template_names

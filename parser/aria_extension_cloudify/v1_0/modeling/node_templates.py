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
from aria.utils import safe_repr

class Scalable(object):
    """
    Only `default_instances` is used in Cloudify DSL v1.0 to v1.2.
    
    `min_instances` and `max_instances` were introduced in Cloudify DSL v1.3.
    """
    
    def __init__(self):
        self.default_instances = 1
        self.min_instances = 0
        self.max_instances = -1
        
    def validate(self, context, presentation, locator):
        def report(name, value, exception):
            context.validation.report('"%s" property in "scalable" capability in node template "%s" is not a valid integer: %s' % (name, presentation._fullname, safe_repr(value)), locator=locator, level=Issue.FIELD, exception=e)

        try:
            self.min_instances = int(self.min_instances)
            if self.min_instances < 0:
                context.validation.report('"min_instances" property in "scalable" capability in node template "%s" is less than 0: %s' % (presentation._fullname, safe_repr(self.min_instances)), locator=locator, level=Issue.FIELD)
        except ValueError as e:
            report('min_instances', self.min_instances, e)
            self.min_instances = 0
        
        if self.max_instances == 'UNBOUNDED':
            self.max_instances = -1
        try:
            self.max_instances = int(self.max_instances)
            if self.max_instances < -1:
                context.validation.report('"max_instances" property in "scalable" capability in node template "%s" is less than -1: %s' % (presentation._fullname, safe_repr(self.max_instances)), locator=locator, level=Issue.FIELD)
            elif (self.max_instances != -1) and (self.max_instances < self.min_instances):
                context.validation.report('"max_instances" property in "scalable" capability in node template "%s" is less than "min_instances": %s' % (presentation._fullname, safe_repr(self.max_instances)), locator=locator, level=Issue.BETWEEN_FIELDS)
        except ValueError as e:
            report('max_instances', self.max_instances, e)
            self.max_instances = -1
        
        try:
            self.default_instances = int(self.default_instances)
            if self.max_instances == -1:
                if self.default_instances < self.min_instances:
                    context.validation.report('"default_instances" property in "scalable" capability in node template "%s" is less than "min_instances": %s' % (presentation._fullname, safe_repr(self.default_instances)), locator=locator, level=Issue.BETWEEN_FIELDS)
            elif (self.default_instances < self.min_instances) or (self.default_instances > self.max_instances):
                context.validation.report('"default_instances" property in "scalable" capability in node template "%s" is not bound between "min_instances" and "max_instances": %s' % (presentation._fullname, safe_repr(self.default_instances)), locator=locator, level=Issue.BETWEEN_FIELDS)
        except ValueError as e:
            report('default_instances', self.default_instances, e)
            self.default_instances = 1

def get_node_template_scalable(context, presentation):
    scalable = Scalable()
    
    instances = presentation.instances
    if instances is not None:
        scalable.default_instances = instances.deploy
        scalable.validate(context, presentation, instances._locator)

    return scalable

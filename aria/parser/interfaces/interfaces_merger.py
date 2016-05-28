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

from itertools import chain


class InterfacesMerger(object):
    def __init__(self,
                 overriding_interfaces,
                 overridden_interfaces,
                 operation_merger):
        self.overriding_interfaces = overriding_interfaces
        self.overridden_interfaces = overridden_interfaces
        self.operation_merger = operation_merger

    def merge(self):
        merged_interfaces = {}
        for name, overriding, overridden in self._merge_dicts_iter(
                self.overriding_interfaces, self.overridden_interfaces, default={}):
            merged_interface = self.merge_interface(overriding, overridden)
            merged_interfaces[name] = merged_interface
        return merged_interfaces

    def merge_interface(self, overriding_dict, overridden_dict):
        merged_interface = {}
        for name, overriding, overridden in self._merge_dicts_iter(
                overriding_dict, overridden_dict):
            merged_operation = self.operation_merger(
                overriding_operation=overriding,
                overridden_operation=overridden).merge()
            merged_interface[name] = merged_operation
        return merged_interface

    def _merge_dicts_iter(self, overriding_dict, overridden_dict, default=None):
        for key in set(chain(overriding_dict.iterkeys(), overridden_dict.iterkeys())):
            yield key, overriding_dict.get(key, default), overridden_dict.get(key, default)

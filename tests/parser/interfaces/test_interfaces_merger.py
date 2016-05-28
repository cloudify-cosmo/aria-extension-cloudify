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

import testtools

from aria.parser.interfaces.interfaces_merger import InterfacesMerger
from aria.parser.interfaces.operation_merger import OperationMerger


class MockOperationMerger(OperationMerger):
    def merge(self):
        return None


class InterfaceMergerTest(testtools.TestCase):
    def _assert_interface(
            self,
            overriding_interface,
            overridden_interface,
            expected_merged_interface_keys):
        merger = InterfacesMerger(None, None, operation_merger=MockOperationMerger)
        merged = merger.merge_interface(overriding_interface, overridden_interface)
        actual_merged_interface_keys = set(merged.keys())
        self.assertEqual(expected_merged_interface_keys, actual_merged_interface_keys)

    def test_merge_operations(self):
        self._assert_interface(
            overriding_interface={'stop': None},
            overridden_interface={'start': None},
            expected_merged_interface_keys=set(['stop', 'start'])
        )

    def test_override_operation(self):
        self._assert_interface(
            overriding_interface={'stop': None},
            overridden_interface={'stop': None},
            expected_merged_interface_keys=set(['stop'])
        )


class InterfacesMergerTest(testtools.TestCase):
    def _assert_interfaces(self,
                           overriding_interfaces,
                           overridden_interfaces,
                           expected_merged_interfaces_keys):
        merger = InterfacesMerger(
            overriding_interfaces=overriding_interfaces,
            overridden_interfaces=overridden_interfaces,
            operation_merger=MockOperationMerger)
        actual_merged_interfaces_keys = set(merger.merge().iterkeys())
        self.assertEqual(expected_merged_interfaces_keys, actual_merged_interfaces_keys)

    def test_merge_interfaces(self):
        self._assert_interfaces(
            overriding_interfaces={'interface1': {}},
            overridden_interfaces={'interface2': {}},
            expected_merged_interfaces_keys=set(['interface1', 'interface2']))

    def test_override_interface(self):
        self._assert_interfaces(
            overriding_interfaces={'interface1': {}},
            overridden_interfaces={'interface1': {}},
            expected_merged_interfaces_keys=set(['interface1'])
        )

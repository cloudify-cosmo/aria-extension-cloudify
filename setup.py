#!/usr/bin/env python
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

import os
from setuptools import setup, find_packages


with open('requirements.txt') as requirements:
    install_requires = requirements.readlines()
try:
    from collections import OrderedDict  # NOQA
except ImportError, e:
    install_requires.append('ordereddict==1.1')
try:
    import importlib  # NOQA
except ImportError:
    install_requires.append('importlib')

package_name = 'aria'
__version__ = '0.0.0.1'
execfile(os.path.join('.', package_name, 'version.py'))

setup(
    name=package_name,
    version=__version__,
    author='aria-core',
    author_email='cosmo-admin@gigaspaces.com',
    packages=find_packages(),
    license='LICENSE',
    description='Aria Project',
    zip_safe=False,
    install_requires=install_requires
)

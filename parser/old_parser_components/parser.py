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

from aria import install_aria_extensions
from aria.consumption import ConsumptionContext, ConsumerChain, Read, Validate, Model, Instance
from aria.loading import UriLocation, LiteralLocation
from aria_extension_cloudify import ClassicDeploymentPlan
from aria_extension_cloudify.v1_3 import CloudifyPresenter1_3
import os

install_aria_extensions()

def parse_from_path(dsl_file_path, resources_base_url=None, additional_resource_sources=(), validate_version=True, **legacy):
    paths = []
    path = os.path.dirname(dsl_file_path)
    if path:
        paths.append(path)
    if resources_base_url:
        paths.append(resources_base_url)
    paths += additional_resource_sources
    return _parse(UriLocation(dsl_file_path), paths, validate_version)

def parse(dsl_string, resources_base_url=None, validate_version=True, **legacy):
    prefixes = [resources_base_url] if resources_base_url is not None else []
    return _parse(LiteralLocation(dsl_string), prefixes, validate_version)

def _parse(location, prefixes, validate_version):
    context = ConsumptionContext()
    context.presentation.print_exceptions = True # Developers, developers, developers, developers
    context.presentation.location = location

    if not validate_version:
        context.presentation.presenter_class = CloudifyPresenter1_3
    
    if prefixes:
        context.loading.prefixes += prefixes
    
    consumer = ConsumerChain(context, (Read, Validate, Model, Instance, ClassicDeploymentPlan))
    consumer.consume()
    
    if not context.validation.has_issues:
        # Check for no content
        raw = context.presentation.presenter._raw if context.presentation.presenter else None
        if (not raw) or ((len(raw) == 1) and ('tosca_definitions_version' in raw)):
            context.validation.report('no content')
        else:
            # Check for no node templates
            if (context.modeling.model) and (not context.modeling.model.node_templates):
                context.validation.report('no node templates')
        
    context.validation.dump_issues()

    return context


import copy

from tosca_parser.framework.elements.node_templates import NodeTemplateRelationships, NodeTemplates
from tosca_parser.framework.elements.node_types import NodeTypes
from tosca_parser.framework.elements.blueprint import Blueprint
from tosca_parser.framework.elements.policies import PolicyTriggers
from tosca_parser.framework.elements.operation import NodeTypeOperation, NodeTemplateOperation, Interface, Operation, OperationExecutor
from tosca_parser.framework.elements.plugins import Plugin
# from tosca_parser.framework.elements. import
# from tosca_parser.framework.elements. import
from tosca_parser.framework.elements import Element, Leaf
from tosca_parser.constants import (
    CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT, POLICY_TRIGGERS,
    PLUGINS, PLUGIN_EXECUTOR_KEY, PLUGINS_TO_INSTALL,
    DEPLOYMENT_PLUGINS_TO_INSTALL,
)
from tosca_parser.extension_tools import ElementExtension
from tosca_parser.exceptions import DSLParsingLogicException


class CloudifyNodeTemplateRelationships(NodeTemplateRelationships):
    CONTAINED_IN_REL_TYPE = 'cloudify.relationships.contained_in'
cloudify_node_template_relationshios_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTemplateRelationships,
    new_element=CloudifyNodeTemplateRelationships)


class CloudifyNodeTypes(NodeTypes):
    HOST_TYPE = 'cloudify.nodes.Compute'
cloudify_node_type_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTypes,
    new_element=CloudifyNodeTypes)


class CloudifyBlueprint(Blueprint):
    schema = dict(
        policy_triggers=PolicyTriggers,
        **Blueprint.schema)

    def parse(self, *args, **kwargs):
        plan = super(CloudifyBlueprint, self).parent(*args, **kwargs)
        plan[POLICY_TRIGGERS] = self.child(PolicyTriggers).value
        return plan
cloudify_blueprint_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=Blueprint,
    new_element=CloudifyBlueprint)


class CloudifyOperationExecutor(OperationExecutor):
    valid_executors = [CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT]

cloudify_operation_executor_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=OperationExecutor,
    new_element=CloudifyOperationExecutor)


class PluginExecutor(Element):
    required = True
    schema = Leaf(type=str)

    def validate(self):
        if self.initial_value not in [CENTRAL_DEPLOYMENT_AGENT, HOST_AGENT]:
            raise DSLParsingLogicException(
                18,
                "Plugin '{0}' has an illegal "
                "'{1}' value '{2}'; value "
                "must be either '{3}' or '{4}'"
                .format(self.ancestor(Plugin).name,
                        self.name,
                        self.initial_value,
                        CENTRAL_DEPLOYMENT_AGENT,
                        HOST_AGENT))
cloudify_plugin_extension_extension = ElementExtension(
    action=ElementExtension.ADD_ELEMENT_TO_SCHEMA_ACTION,
    target_element=Plugin,
    new_element=PluginExecutor,
    schema_key='executor')


class CloudifyNodeTemplates(NodeTemplates):
    @staticmethod
    def check_executor_key(plugin):
        return plugin[PLUGIN_EXECUTOR_KEY] == HOST_AGENT
cloudify_node_templates_extension = ElementExtension(
    action=ElementExtension.REPLACE_ELEMENT_ACTION,
    target_element=NodeTemplates,
    new_element=CloudifyNodeTemplates)

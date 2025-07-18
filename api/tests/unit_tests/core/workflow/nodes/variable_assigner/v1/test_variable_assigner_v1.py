import time
import uuid
from unittest import mock
from uuid import uuid4

from core.app.entities.app_invoke_entities import InvokeFrom
from core.variables import ArrayStringVariable, StringVariable
from core.workflow.conversation_variable_updater import ConversationVariableUpdater
from core.workflow.entities.variable_pool import VariablePool
from core.workflow.graph_engine.entities.graph import Graph
from core.workflow.graph_engine.entities.graph_init_params import GraphInitParams
from core.workflow.graph_engine.entities.graph_runtime_state import GraphRuntimeState
from core.workflow.nodes.variable_assigner.v1 import VariableAssignerNode
from core.workflow.nodes.variable_assigner.v1.node_data import WriteMode
from core.workflow.system_variable import SystemVariable
from models.enums import UserFrom
from models.workflow import WorkflowType

DEFAULT_NODE_ID = "node_id"


def test_overwrite_string_variable():
    graph_config = {
        "edges": [
            {
                "id": "start-source-assigner-target",
                "source": "start",
                "target": "assigner",
            },
        ],
        "nodes": [
            {"data": {"type": "start"}, "id": "start"},
            {
                "data": {
                    "type": "assigner",
                },
                "id": "assigner",
            },
        ],
    }

    graph = Graph.init(graph_config=graph_config)

    init_params = GraphInitParams(
        tenant_id="1",
        app_id="1",
        workflow_type=WorkflowType.WORKFLOW,
        workflow_id="1",
        graph_config=graph_config,
        user_id="1",
        user_from=UserFrom.ACCOUNT,
        invoke_from=InvokeFrom.DEBUGGER,
        call_depth=0,
    )

    conversation_variable = StringVariable(
        id=str(uuid4()),
        name="test_conversation_variable",
        value="the first value",
    )

    input_variable = StringVariable(
        id=str(uuid4()),
        name="test_string_variable",
        value="the second value",
    )
    conversation_id = str(uuid.uuid4())

    # construct variable pool
    variable_pool = VariablePool(
        system_variables=SystemVariable(conversation_id=conversation_id),
        user_inputs={},
        environment_variables=[],
        conversation_variables=[conversation_variable],
    )

    variable_pool.add(
        [DEFAULT_NODE_ID, input_variable.name],
        input_variable,
    )

    mock_conv_var_updater = mock.Mock(spec=ConversationVariableUpdater)
    mock_conv_var_updater_factory = mock.Mock(return_value=mock_conv_var_updater)

    node = VariableAssignerNode(
        id=str(uuid.uuid4()),
        graph_init_params=init_params,
        graph=graph,
        graph_runtime_state=GraphRuntimeState(variable_pool=variable_pool, start_at=time.perf_counter()),
        config={
            "id": "node_id",
            "data": {
                "title": "test",
                "assigned_variable_selector": ["conversation", conversation_variable.name],
                "write_mode": WriteMode.OVER_WRITE.value,
                "input_variable_selector": [DEFAULT_NODE_ID, input_variable.name],
            },
        },
        conv_var_updater_factory=mock_conv_var_updater_factory,
    )

    list(node.run())
    expected_var = StringVariable(
        id=conversation_variable.id,
        name=conversation_variable.name,
        description=conversation_variable.description,
        selector=conversation_variable.selector,
        value_type=conversation_variable.value_type,
        value=input_variable.value,
    )
    mock_conv_var_updater.update.assert_called_once_with(conversation_id=conversation_id, variable=expected_var)
    mock_conv_var_updater.flush.assert_called_once()

    got = variable_pool.get(["conversation", conversation_variable.name])
    assert got is not None
    assert got.value == "the second value"
    assert got.to_object() == "the second value"


def test_append_variable_to_array():
    graph_config = {
        "edges": [
            {
                "id": "start-source-assigner-target",
                "source": "start",
                "target": "assigner",
            },
        ],
        "nodes": [
            {"data": {"type": "start"}, "id": "start"},
            {
                "data": {
                    "type": "assigner",
                },
                "id": "assigner",
            },
        ],
    }

    graph = Graph.init(graph_config=graph_config)

    init_params = GraphInitParams(
        tenant_id="1",
        app_id="1",
        workflow_type=WorkflowType.WORKFLOW,
        workflow_id="1",
        graph_config=graph_config,
        user_id="1",
        user_from=UserFrom.ACCOUNT,
        invoke_from=InvokeFrom.DEBUGGER,
        call_depth=0,
    )

    conversation_variable = ArrayStringVariable(
        id=str(uuid4()),
        name="test_conversation_variable",
        value=["the first value"],
    )

    input_variable = StringVariable(
        id=str(uuid4()),
        name="test_string_variable",
        value="the second value",
    )
    conversation_id = str(uuid.uuid4())

    variable_pool = VariablePool(
        system_variables=SystemVariable(conversation_id=conversation_id),
        user_inputs={},
        environment_variables=[],
        conversation_variables=[conversation_variable],
    )
    variable_pool.add(
        [DEFAULT_NODE_ID, input_variable.name],
        input_variable,
    )

    mock_conv_var_updater = mock.Mock(spec=ConversationVariableUpdater)
    mock_conv_var_updater_factory = mock.Mock(return_value=mock_conv_var_updater)

    node = VariableAssignerNode(
        id=str(uuid.uuid4()),
        graph_init_params=init_params,
        graph=graph,
        graph_runtime_state=GraphRuntimeState(variable_pool=variable_pool, start_at=time.perf_counter()),
        config={
            "id": "node_id",
            "data": {
                "title": "test",
                "assigned_variable_selector": ["conversation", conversation_variable.name],
                "write_mode": WriteMode.APPEND.value,
                "input_variable_selector": [DEFAULT_NODE_ID, input_variable.name],
            },
        },
        conv_var_updater_factory=mock_conv_var_updater_factory,
    )

    list(node.run())
    expected_value = list(conversation_variable.value)
    expected_value.append(input_variable.value)
    expected_var = ArrayStringVariable(
        id=conversation_variable.id,
        name=conversation_variable.name,
        description=conversation_variable.description,
        selector=conversation_variable.selector,
        value_type=conversation_variable.value_type,
        value=expected_value,
    )
    mock_conv_var_updater.update.assert_called_once_with(conversation_id=conversation_id, variable=expected_var)
    mock_conv_var_updater.flush.assert_called_once()

    got = variable_pool.get(["conversation", conversation_variable.name])
    assert got is not None
    assert got.to_object() == ["the first value", "the second value"]


def test_clear_array():
    graph_config = {
        "edges": [
            {
                "id": "start-source-assigner-target",
                "source": "start",
                "target": "assigner",
            },
        ],
        "nodes": [
            {"data": {"type": "start"}, "id": "start"},
            {
                "data": {
                    "type": "assigner",
                },
                "id": "assigner",
            },
        ],
    }

    graph = Graph.init(graph_config=graph_config)

    init_params = GraphInitParams(
        tenant_id="1",
        app_id="1",
        workflow_type=WorkflowType.WORKFLOW,
        workflow_id="1",
        graph_config=graph_config,
        user_id="1",
        user_from=UserFrom.ACCOUNT,
        invoke_from=InvokeFrom.DEBUGGER,
        call_depth=0,
    )

    conversation_variable = ArrayStringVariable(
        id=str(uuid4()),
        name="test_conversation_variable",
        value=["the first value"],
    )

    conversation_id = str(uuid.uuid4())
    variable_pool = VariablePool(
        system_variables=SystemVariable(conversation_id=conversation_id),
        user_inputs={},
        environment_variables=[],
        conversation_variables=[conversation_variable],
    )

    mock_conv_var_updater = mock.Mock(spec=ConversationVariableUpdater)
    mock_conv_var_updater_factory = mock.Mock(return_value=mock_conv_var_updater)

    node = VariableAssignerNode(
        id=str(uuid.uuid4()),
        graph_init_params=init_params,
        graph=graph,
        graph_runtime_state=GraphRuntimeState(variable_pool=variable_pool, start_at=time.perf_counter()),
        config={
            "id": "node_id",
            "data": {
                "title": "test",
                "assigned_variable_selector": ["conversation", conversation_variable.name],
                "write_mode": WriteMode.CLEAR.value,
                "input_variable_selector": [],
            },
        },
        conv_var_updater_factory=mock_conv_var_updater_factory,
    )

    list(node.run())
    expected_var = ArrayStringVariable(
        id=conversation_variable.id,
        name=conversation_variable.name,
        description=conversation_variable.description,
        selector=conversation_variable.selector,
        value_type=conversation_variable.value_type,
        value=[],
    )
    mock_conv_var_updater.update.assert_called_once_with(conversation_id=conversation_id, variable=expected_var)
    mock_conv_var_updater.flush.assert_called_once()

    got = variable_pool.get(["conversation", conversation_variable.name])
    assert got is not None
    assert got.to_object() == []

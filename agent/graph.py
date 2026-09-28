from langgraph.graph import StateGraph, START, END

from agent.state import AgentState

from agent.nodes import (
    identify_intent,
    extract_member_id,
    retrieve_node,
    tool_node,
    validate_node,
    escalation_node,
    generate_response,
)


def prepare_request(state: AgentState):
    """
    Prepare the incoming user request.

    Identifies the user's intent and extracts a member ID
    when one is present in the query.
    """

    query = state["query"]

    state["intent"] = identify_intent(query)
    state["member_id"] = extract_member_id(query)

    state["trace"] = [
        f"Intent identified: {state['intent']}"
    ]

    return state


def build_graph():
    """
    Build the LangGraph agent workflow.

    Workflow:

    START
       ↓
    Prepare Request
       ↓
    Retrieve Knowledge
       ↓
    Execute Tools
       ↓
    Validate
       ↓
    Human Escalation
       ↓
    Generate Response
       ↓
    END
    """

    graph = StateGraph(AgentState)

    # ---------------------------------------------------------
    # Add nodes
    # ---------------------------------------------------------

    graph.add_node(
        "prepare_request",
        prepare_request
    )

    graph.add_node(
        "retrieve",
        retrieve_node
    )

    graph.add_node(
        "tools",
        tool_node
    )

    graph.add_node(
        "validate",
        validate_node
    )

    graph.add_node(
        "escalation",
        escalation_node
    )

    graph.add_node(
        "generate_response",
        generate_response
    )

    # ---------------------------------------------------------
    # Define workflow
    # ---------------------------------------------------------

    graph.add_edge(
        START,
        "prepare_request"
    )

    graph.add_edge(
        "prepare_request",
        "retrieve"
    )

    graph.add_edge(
        "retrieve",
        "tools"
    )

    graph.add_edge(
        "tools",
        "validate"
    )

    graph.add_edge(
        "validate",
        "escalation"
    )

    graph.add_edge(
        "escalation",
        "generate_response"
    )

    graph.add_edge(
        "generate_response",
        END
    )

    # ---------------------------------------------------------
    # Compile graph
    # ---------------------------------------------------------

    return graph.compile()
import re

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


# ============================================================
# CONVERSATION FOLLOW-UP DETECTION
# ============================================================

def is_follow_up(query: str, previous_intent: str) -> bool:
    """
    Decide whether a general-classified message is a follow-up
    to the previous loyalty-service request.
    """
    if not previous_intent or previous_intent == "general":
        return False

    text = str(query or "").strip().lower()

    # Explicit new/general questions should not inherit old intent.
    new_request_patterns = (
        r"\bwhat (?:services|features) (?:can|do) you\b",
        r"\bwhat can you (?:do|help me with)\b",
        r"\bwho are you\b",
        r"\bhelp menu\b",
        r"\bstart (?:over|again)\b",
        r"\bnew (?:conversation|enquiry|request)\b",
    )
    if any(re.search(p, text) for p in new_request_patterns):
        return False

    # A member-ID-only reply is a follow-up.
    member_id = extract_member_id(text)
    without_id = re.sub(
        r"\bM\d{3}\b", "", text, flags=re.IGNORECASE
    )
    without_id = re.sub(
        r"\b(my|member|membership|id|number|is|it's|it|the)\b",
        "", without_id, flags=re.IGNORECASE
    )
    without_id = re.sub(r"[\s.,:;!?'-]+", "", without_id)

    if member_id and not without_id:
        return True

    # Common follow-up expressions.
    follow_up_patterns = (
        r"^(?:yes|no|okay|ok|sure|please|continue)\b",
        r"\b(?:how many|how much|what about|what is the status)\b",
        r"\b(?:still missing|those miles|that transaction)\b",
        r"\b(?:my account|my status|my balance)\b",
        r"\b(?:can you check|please check|check again)\b",
        r"\b(?:tell me more|explain that|why is that)\b",
        r"\b(?:same member|same account)\b",
    )

    return any(re.search(p, text) for p in follow_up_patterns)


# ============================================================
# PREPARE REQUEST WITH CONVERSATION CONTEXT
# ============================================================

def prepare_request(state: AgentState) -> AgentState:
    """
    Identify the current intent and member ID.

    The Streamlit application supplies previous context through
    the initial LangGraph state.
    """

    query = str(state.get("query", "") or "")

    previous_intent = state.get("intent", "") or ""
    previous_member_id = state.get("member_id", "") or ""

    detected_intent = identify_intent(query)
    detected_member_id = extract_member_id(query)

    if detected_intent != "general":
        active_intent = detected_intent
        context_source = "Current message"

    elif is_follow_up(query, previous_intent):
        active_intent = previous_intent
        context_source = "Previous conversation"

    else:
        active_intent = "general"
        context_source = "General request"

    active_member_id = detected_member_id or previous_member_id

    state["intent"] = active_intent
    state["member_id"] = active_member_id

    # Reset execution trace for this message.
    state["trace"] = [
        f"Intent identified: {active_intent}",
        f"Member ID: {active_member_id or 'Not provided'}",
        f"Intent context source: {context_source}",
    ]

    return state


# ============================================================
# BUILD LANGGRAPH WORKFLOW
# ============================================================

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("prepare_request", prepare_request)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("escalation", escalation_node)
    workflow.add_node("generate_response", generate_response)

    workflow.add_edge(START, "prepare_request")
    workflow.add_edge("prepare_request", "retrieve")
    workflow.add_edge("retrieve", "tools")
    workflow.add_edge("tools", "validate")
    workflow.add_edge("validate", "escalation")
    workflow.add_edge("escalation", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
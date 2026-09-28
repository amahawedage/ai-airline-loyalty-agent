from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # Original user request
    query: str

    # Identified loyalty scenario
    intent: str

    # Identifiers extracted from the query
    member_id: str
    transaction_id: str

    # RAG information
    retrieved_context: list[str]
    retrieved_sources: list[str]

    # Python tool results
    tool_results: dict[str, Any]

    # Validation
    validation_status: str
    validation_message: str

    # Escalation
    escalation_required: bool
    escalation_reason: str

    # Final response
    response: str

    # Traceability
    trace: list[str]
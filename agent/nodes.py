import re
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.prompts import SYSTEM_PROMPT
from rag.retrieve import retrieve_knowledge
from tools.member_tools import get_member_details
from tools.transaction_tools import check_missing_miles
from tools.reward_tools import check_reward_eligibility
from tools.family_tools import get_family_account
from tools.partner_tools import check_partner_airline
from tools.tier_tools import calculate_tier_upgrade
from tools.escalation_tools import create_human_escalation
# ============================================================
# INTENT IDENTIFICATION
# ============================================================
def identify_intent(query: str):
    query_lower = query.lower().strip()
    # --------------------------------------------------------
    # Missing Miles
    # --------------------------------------------------------
    if (
        "missing mile" in query_lower
        or "miles are missing" in query_lower
        or "missing miles" in query_lower
        or (
            "flight miles" in query_lower
            and "missing" in query_lower
        )
        or "miles not credited" in query_lower
        or "miles haven't been credited" in query_lower
        or "miles have not been credited" in query_lower
    ):
        return "missing_miles"
    # --------------------------------------------------------
    # Tier Upgrade
    # --------------------------------------------------------
    if (
        "tier upgrade" in query_lower
        or "tier status" in query_lower
        or "upgrade my tier" in query_lower
        or "tier qualification" in query_lower
        or "tier miles" in query_lower
        or "silver tier" in query_lower
        or "gold tier" in query_lower
    ):
        return "tier_upgrade"
    # --------------------------------------------------------
    # Reward Booking
    # --------------------------------------------------------
    if (
        "reward booking" in query_lower
        or "reward book" in query_lower
        or "book a reward" in query_lower
        or "book reward" in query_lower
        or "reward flight" in query_lower
        or "reward ticket" in query_lower
        or "redeem miles" in query_lower
        or "redeem my miles" in query_lower
        or (
            "book" in query_lower
            and (
                "miles" in query_lower
                or "economy" in query_lower
                or "business" in query_lower
                or "reward" in query_lower
            )
        )
    ):
        return "reward_booking"
    # --------------------------------------------------------
    # Family Account
    # --------------------------------------------------------
    if (
        "family account" in query_lower
        or "family members" in query_lower
        or "family member" in query_lower
        or "family programme" in query_lower
        or "family program" in query_lower
    ):
        return "family_account"
    # --------------------------------------------------------
    # Partner Airline
    # --------------------------------------------------------
    if (
        "partner airline" in query_lower
        or "partner airlines" in query_lower
        or "partner air" in query_lower
        or (
            "partner" in query_lower
            and (
                "airline" in query_lower
                or "flight" in query_lower
                or "miles" in query_lower
                or "earn" in query_lower
                or "redeem" in query_lower
            )
        )
        or "earn miles on" in query_lower
        or "earn miles with" in query_lower
        or "miles on" in query_lower
        or "miles with" in query_lower
    ):
        return "partner_airline"
    return "general"
# ============================================================
# MEMBER ID EXTRACTION
# ============================================================
def extract_member_id(query: str):
    match = re.search(r"\bM\d{3}\b", query.upper())
    if match:
        return match.group(0)
    return ""
# ============================================================
# REWARD BOOKING INPUT EXTRACTION
# ============================================================
def extract_reward_booking_details(query: str):
    """
    Extract origin, destination and cabin from a reward-booking query.
    Supported examples:
    DXB to LHR Economy
    DXB to SIN Economy
    DXB-LHR Business
    DXB → SIN Economy
    DXB/SIN Economy
    Returns:
        {
            "origin": "...",
            "destination": "...",
            "cabin": "..."
        }
    """
    query_upper = query.upper()
    origin = ""
    destination = ""
    cabin = ""
    # --------------------------------------------------------
    # Extract airport codes
    # --------------------------------------------------------
    airport_codes = re.findall(
        r"\b[A-Z]{3}\b",
        query_upper
    )
    # Remove M001/M002 etc. if they somehow appear
    airport_codes = [
        code
        for code in airport_codes
        if not re.fullmatch(r"M\d{3}", code)
    ]
    # Common airport codes used in this prototype
    known_airports = {
        "DXB",
        "LHR",
        "SIN",
        "SYD",
    }
    airport_codes = [
        code
        for code in airport_codes
        if code in known_airports
    ]
    if len(airport_codes) >= 2:
        origin = airport_codes[0]
        destination = airport_codes[1]
    # --------------------------------------------------------
    # Extract cabin
    # --------------------------------------------------------
    if "ECONOMY" in query_upper:
        cabin = "Economy"
    elif "BUSINESS" in query_upper:
        cabin = "Business"
    return {
        "origin": origin,
        "destination": destination,
        "cabin": cabin,
    }
# ============================================================
# RAG RETRIEVAL NODE
# ============================================================
def retrieve_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    documents = retrieve_knowledge(query, k=3)
    state["retrieved_context"] = [
        doc.page_content for doc in documents
    ]
    state["retrieved_sources"] = [
        doc.metadata.get("source", "Unknown")
        for doc in documents
    ]
    state.setdefault("trace", []).append(
        f"RAG retrieval completed: {len(documents)} documents"
    )
    return state
# ============================================================
# TOOL EXECUTION NODE
# ============================================================
def tool_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "")
    member_id = state.get("member_id", "")
    query = state.get("query", "")
    tool_results = {}
    # --------------------------------------------------------
    # Missing Miles
    # --------------------------------------------------------
    if intent == "missing_miles":
        if member_id:
            result = check_missing_miles(member_id)
            tool_results["missing_miles"] = result
        else:
            tool_results["missing_miles"] = {
                "success": False,
                "message": "Member ID is required to check missing miles."
            }
    # --------------------------------------------------------
    # Tier Upgrade
    # --------------------------------------------------------
    elif intent == "tier_upgrade":
        if member_id:
            result = calculate_tier_upgrade(member_id)
            tool_results["tier_upgrade"] = result
        else:
            tool_results["tier_upgrade"] = {
                "success": False,
                "message": "Member ID is required to calculate tier upgrade status."
            }
    # --------------------------------------------------------
    # Reward Booking
    # --------------------------------------------------------
    elif intent == "reward_booking":
        reward_details = extract_reward_booking_details(query)
        origin = reward_details["origin"]
        destination = reward_details["destination"]
        cabin = reward_details["cabin"]
        # Store extracted details in trace for transparency
        state.setdefault("trace", []).append(
            f"Reward booking details extracted: "
            f"{origin or 'N/A'} -> "
            f"{destination or 'N/A'}, "
            f"{cabin or 'N/A'}"
        )
        if member_id and origin and destination and cabin:
            result = check_reward_eligibility(
                member_id,
                origin,
                destination,
                cabin
            )
            tool_results["reward_booking"] = result
        else:
            missing_fields = []
            if not member_id:
                missing_fields.append("member ID")
            if not origin:
                missing_fields.append("origin")
            if not destination:
                missing_fields.append("destination")
            if not cabin:
                missing_fields.append("cabin")
            tool_results["reward_booking"] = {
                "success": False,
                "message": (
                    "The following information is required: "
                    + ", ".join(missing_fields)
                    + "."
                )
            }
    # --------------------------------------------------------
    # Family Account
    # --------------------------------------------------------
    elif intent == "family_account":
        if member_id:
            result = get_family_account(member_id)
            tool_results["family_account"] = result
        else:
            tool_results["family_account"] = {
                "success": False,
                "message": "Member ID is required to retrieve family account information."
            }
    # --------------------------------------------------------
    # Partner Airline
    # --------------------------------------------------------
    elif intent == "partner_airline":
        query_lower = query.lower()
        partner_name = ""
        if "partner air" in query_lower:
            partner_name = "Partner Air"
        elif "global connect" in query_lower:
            partner_name = "Global Connect"
        else:
            # Try to identify a partner name after "on"
            match = re.search(
                r"(?:on|with)\s+([A-Za-z ]+?)(?:\?|$)",
                query,
                re.IGNORECASE
            )
            if match:
                partner_name = match.group(1).strip()
        if partner_name:
            result = check_partner_airline(partner_name)
            tool_results["partner_airline"] = result
        else:
            tool_results["partner_airline"] = {
                "success": False,
                "message": "Partner airline name is required."
            }
    # --------------------------------------------------------
    # General Request
    # --------------------------------------------------------
    else:
        tool_results["general"] = {
            "success": True,
            "message": "No specific tool required for this request."
        }
    state["tool_results"] = tool_results
    state.setdefault("trace", []).append(
        f"Tool execution completed for intent: {intent}"
    )
    return state
# ============================================================
# VALIDATION NODE
# ============================================================
def validate_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "")
    member_id = state.get("member_id", "")
    tool_results = state.get("tool_results", {})
    validation_status = "PASS"
    validation_message = "Request validated successfully."
    escalation_required = False
    escalation_reason = ""
    # --------------------------------------------------------
    # Member ID validation
    # --------------------------------------------------------
    member_required_intents = {
        "missing_miles",
        "tier_upgrade",
        "reward_booking",
        "family_account",
    }
    if intent in member_required_intents and not member_id:
        validation_status = "ESCALATE"
        validation_message = "Member ID is required."
        escalation_required = True
        escalation_reason = "Member ID is required to process the request."
    # --------------------------------------------------------
    # Tool result validation
    # --------------------------------------------------------
    if intent == "missing_miles" and member_id:
        result = tool_results.get("missing_miles", {})
        if not result.get("success"):
            validation_status = "ESCALATE"
            validation_message = result.get(
                "message",
                "Missing miles information could not be retrieved."
            )
            escalation_required = True
            escalation_reason = validation_message
    elif intent == "tier_upgrade" and member_id:
        result = tool_results.get("tier_upgrade", {})
        if not result.get("success"):
            validation_status = "ESCALATE"
            validation_message = result.get(
                "message",
                "Tier upgrade information could not be retrieved."
            )
            escalation_required = True
            escalation_reason = validation_message
    elif intent == "reward_booking":
        result = tool_results.get("reward_booking", {})
        if not result.get("success"):
            validation_status = "ESCALATE"
            validation_message = result.get(
                "message",
                "Reward eligibility could not be evaluated."
            )
            escalation_required = True
            escalation_reason = validation_message
    elif intent == "family_account" and member_id:
        result = tool_results.get("family_account", {})
        if not result.get("success"):
            validation_status = "ESCALATE"
            validation_message = result.get(
                "message",
                "Family account information could not be retrieved."
            )
            escalation_required = True
            escalation_reason = validation_message
    elif intent == "partner_airline":
        result = tool_results.get("partner_airline", {})
        if not result.get("success"):
            validation_status = "ESCALATE"
            validation_message = result.get(
                "message",
                "Partner airline information could not be retrieved."
            )
            escalation_required = True
            escalation_reason = validation_message
    state["validation_status"] = validation_status
    state["validation_message"] = validation_message
    state["escalation_required"] = escalation_required
    state["escalation_reason"] = escalation_reason
    state.setdefault("trace", []).append(
        f"Validation status: {validation_status}"
    )
    return state
# ============================================================
# HUMAN ESCALATION NODE
# ============================================================
def escalation_node(state: AgentState) -> AgentState:
    escalation_required = state.get(
        "escalation_required",
        False
    )
    if not escalation_required:
        state.setdefault("trace", []).append(
            "Human escalation not required."
        )
        return state
    intent = state.get("intent", "general")
    member_id = state.get("member_id", "")
    query = state.get("query", "")
    reason = state.get(
        "escalation_reason",
        "Additional human review is required."
    )
    result = create_human_escalation(
        scenario=intent,
        member_id=member_id,
        reason=reason,
        query=query,
    )
    state.setdefault("tool_results", {})
    state["tool_results"]["human_escalation"] = result
    if result.get("success"):
        state.setdefault("trace", []).append(
            "Human escalation record created: "
            f"{result.get('escalation_id')}"
        )
    else:
        state.setdefault("trace", []).append(
            "Human escalation creation failed."
        )
    return state
# ============================================================
# RESPONSE GENERATION NODE
# ============================================================
def generate_response(state: AgentState) -> AgentState:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key missing: set GOOGLE_API_KEY in .env or Streamlit secrets.")
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
        temperature=0,
        google_api_key=api_key,
    )
    query = state.get("query", "")
    intent = state.get("intent", "general")
    validation_status = state.get(
        "validation_status",
        "UNKNOWN"
    )
    validation_message = state.get(
        "validation_message",
        ""
    )
    retrieved_context = state.get(
        "retrieved_context",
        []
    )
    tool_results = state.get(
        "tool_results",
        {}
    )
    escalation_required = state.get(
        "escalation_required",
        False
    )
    context_text = "\n\n".join(
        retrieved_context
    )
    user_prompt = f"""
User query:
{query}
Detected intent:
{intent}
Validation status:
{validation_status}
Validation message:
{validation_message}
Retrieved loyalty-policy information:
{context_text}
Tool results:
{tool_results}
Human escalation required:
{escalation_required}
Instructions:
1. Use the retrieved knowledge-base information as policy evidence.
2. Treat Python tool results as authoritative for member-specific information.
3. Do not invent member information.
4. Do not invent transaction information.
5. Do not invent reward availability.
6. Do not invent partner-airline rules.
7. Do not invent tier information.
8. Do not perform business calculations yourself when a tool has already provided the result.
9. If validation failed, clearly explain what information is missing or why the request could not be completed.
10. If human escalation was created, do not claim that a real human case has been submitted. This is a research prototype.
11. Do not claim that a booking, account change, transaction update, or missing-mile request has been completed.
12. Give a concise and useful response.
13. Clearly distinguish between available system information and unavailable information.
This is an MSc research prototype using synthetic member data.
"""
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    content = response.content
    if isinstance(content, str):
        state["response"] = content
    elif isinstance(content, list):
        state["response"] = "\n".join(
            part if isinstance(part, str) else part.get("text", "")
            for part in content
            if isinstance(part, str) or (isinstance(part, dict) and part.get("type") == "text")
        )
    else:
        state["response"] = str(content)
    state.setdefault("trace", []).append("Final response generated by Gemini.")
    return state

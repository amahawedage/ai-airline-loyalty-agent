
import json
import streamlit as st
from agent.graph import build_graph


# ==========================================================
# 1. Page configuration
# ==========================================================
st.set_page_config(
    page_title="Synthetic Airline Loyalty AI Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# 2. Professional airline-themed styling
# ==========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --navy: #102f59;
        --navy-dark: #092448;
        --blue: #2678dc;
        --pale-blue: #eef5ff;
        --text: #183456;
        --muted: #6b809d;
        --border: #e0eaf7;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #f7faff;
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #102f59 0%, #092448 100%
        );
        border-right: none;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 8px 26px 8px;
        margin-bottom: 18px;
        border-bottom: 1px solid rgba(255,255,255,0.18);
    }

    .brand-icon {
        font-size: 34px;
    }

    .brand-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.2px;
    }

    .brand-subtitle {
        font-size: 12px;
        color: #d1e0f5;
        margin-top: 3px;
    }

    .sidebar-caption {
        color: #a9c3e5 !important;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.3px;
        text-transform: uppercase;
        margin: 20px 8px 10px;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 11px 12px;
        color: #f4f8ff;
        font-size: 13px;
        min-height: 42px;
        transition: background 0.2s ease;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.13);
        border-color: rgba(255,255,255,0.1);
    }

    .sidebar-footer {
        color: #b5c8e2 !important;
        font-size: 12px;
        line-height: 1.7;
        padding: 24px 8px 8px;
        margin-top: 28px;
        border-top: 1px solid rgba(255,255,255,0.18);
    }

    .topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 22px;
        color: var(--muted);
        font-size: 12px;
    }

    .status-pill {
        display: inline-block;
        padding: 6px 11px;
        background: #e8f8ef;
        color: #18794e;
        border-radius: 30px;
        font-size: 11px;
        font-weight: 600;
    }

    .hero {
        background:
            radial-gradient(
                circle at 92% 10%,
                rgba(116,177,255,0.22), transparent 30%
            ),
            linear-gradient(120deg, #ffffff, #edf5ff);
        border: 1px solid #e2ecfa;
        border-radius: 20px;
        padding: 34px 32px;
        margin-bottom: 30px;
        box-shadow: 0 6px 24px rgba(28,68,120,0.04);
    }

    .hero-eyebrow {
        font-size: 11px;
        font-weight: 700;
        color: #2878d0;
        letter-spacing: 1.7px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .hero h1 {
        font-size: clamp(27px, 3vw, 39px);
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -1px;
        color: #102f59;
        margin: 0 0 13px 0;
    }

    .hero p {
        font-size: 15px;
        line-height: 1.7;
        color: #657d9e;
        margin: 0;
        max-width: 760px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 750;
        color: #102f59;
        margin: 8px 0 4px;
    }

    .section-subtitle {
        font-size: 13px;
        color: #7186a2;
        margin-bottom: 18px;
    }

    .service-card {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 19px 16px 12px;
        min-height: 188px;
        box-shadow: 0 4px 16px rgba(29,70,122,0.035);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .service-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 22px rgba(29,70,122,0.09);
    }

    .service-icon {
        width: 43px;
        height: 43px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-bottom: 13px;
    }

    .icon-blue { background: #e5f0ff; }
    .icon-green { background: #e1f8ef; }
    .icon-purple { background: #f0e8ff; }
    .icon-orange { background: #fff0e3; }
    .icon-pink { background: #fbe9f7; }

    .service-card h3 {
        color: #17385f;
        font-size: 15px;
        font-weight: 700;
        margin: 0 0 9px 0;
    }

    .service-card p {
        color: #71839d;
        font-size: 12px;
        line-height: 1.65;
        min-height: 57px;
        margin: 0;
    }

    .service-arrow {
        color: #2678dc;
        font-size: 20px;
        font-weight: 600;
        margin-top: 7px;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stChatInput {
        border-radius: 16px !important;
    }

    [data-testid="stChatInput"] {
        border: 1px solid #d9e6f7 !important;
        border-radius: 15px !important;
        background: #ffffff !important;
        box-shadow: 0 5px 20px rgba(30,70,120,0.06);
    }

    [data-testid="stChatInput"] textarea {
        color: #183456 !important;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid #e5edf8;
        border-radius: 14px;
        background: #ffffff;
        padding: 15px;
        margin-bottom: 12px;
    }

    .suggestion-label {
        color: #7a8da7;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-top: 15px;
        margin-bottom: 8px;
    }

    .page-note {
        text-align: center;
        color: #8798ad;
        font-size: 11px;
        padding: 24px 0 10px;
    }

    @media (max-width: 900px) {
        .hero {
            padding: 25px 20px;
        }
        .service-card {
            min-height: 170px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# 3. Initialise the existing LangGraph agent
# ==========================================================
@st.cache_resource
def get_agent():
    return build_graph()


try:
    graph = get_agent()
except Exception as exc:
    graph = None
    agent_initialisation_error = str(exc)
else:
    agent_initialisation_error = None


# ==========================================================
# 4. Session state
# ==========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# ==========================================================
# 5. Scenario definitions
# ==========================================================
SCENARIOS = {
    "Missing Miles": {
        "icon": "◉",
        "style": "icon-pink",
        "description": "Check missing miles, credit status and transaction updates.",
        "query": "My miles are missing. Can you check the transaction status?",
    },
    "Tier Upgrades": {
        "icon": "♕",
        "style": "icon-green",
        "description": "Understand your tier status, qualification and upgrade options.",
        "query": "How can I qualify for a tier upgrade?",
    },
    "Reward Bookings": {
        "icon": "🎁︎",
        "style": "icon-blue",
        "description": "Explore reward bookings, availability and required miles.",
        "query": "Can you help me check a reward flight booking?",
    },
    "Family Accounts": {
        "icon": "👥︎",
        "style": "icon-purple",
        "description": "Get guidance on family accounts and shared miles.",
        "query": "How do family accounts and shared miles work?",
    },
    "Partner Airlines": {
        "icon": "✈",
        "style": "icon-orange",
        "description": "Explore partner-airline earning and redemption rules.",
        "query": "Can I earn or redeem miles with a partner airline?",
    },
}


# ==========================================================
# 6. Professional sidebar
# ==========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">✈</div>
            <div>
                <div class="brand-title">Synthetic Airline</div>
                <div class="brand-subtitle">Loyalty Programme</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-caption">Your services</div>',
        unsafe_allow_html=True,
    )

    if st.button("🏠︎   Home", key="nav_home"):
        st.session_state.pending_query = None
        st.session_state.messages = []
        st.rerun()

    #if st.button("◷   My Enquiries", key="nav_enquiries"):
    #    if st.session_state.messages:
    #        st.session_state.pending_query = None
    #        st.rerun()
    #    else:
    #        st.info("Your enquiries will appear in the conversation area.")

    if st.button("◉   Missing Miles", key="nav_miles"):
        st.session_state.pending_query = (
            "My miles are missing. Can you check the transaction status?"
        )
        st.rerun()

    if st.button("🎁︎   Reward Bookings", key="nav_rewards"):
        st.session_state.pending_query = SCENARIOS["Reward Bookings"]["query"]
        st.rerun()

    if st.button("♕   Tier Upgrades", key="nav_tier"):
        st.session_state.pending_query = SCENARIOS["Tier Upgrades"]["query"]
        st.rerun()

    if st.button("👥︎   Family Accounts", key="nav_family"):
        st.session_state.pending_query = SCENARIOS["Family Accounts"]["query"]
        st.rerun()

    if st.button("✈   Partner Airlines", key="nav_partners"):
        st.session_state.pending_query = SCENARIOS["Partner Airlines"]["query"]
        st.rerun()

    st.markdown(
        """
        <div class="sidebar-footer">
            <strong>More miles. More possibilities.</strong><br>
            Your loyalty programme assistant
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# 7. Main page header
# ==========================================================
st.markdown(
    """
    <div class="topline">
        <span>LOYALTY SERVICES / HOME</span>
        <span class="status-pill">✦ AI ASSISTANT</span>
    </div>

    <div class="hero">
        <div class="hero-eyebrow">Your loyalty journey, made easier</div>
        <h1>Airline Loyalty AI<br>Customer Service Assistant</h1>
        <p>
            Hello!, I can help you with your loyalty programme enquiries,
            explain relevant policies and guide you through your next steps.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# 8. Service cards
# ==========================================================
st.markdown(
    """
    <div class="section-title">How can I help you?</div>
    <div class="section-subtitle">
        Choose a service below or ask me a question in your own words.
    </div>
    """,
    unsafe_allow_html=True,
)

columns = st.columns(5, gap="medium")

for column, (name, scenario) in zip(columns, SCENARIOS.items()):
    with column:
        st.markdown(
            f"""
            <div class="service-card">
                <div class="service-icon {scenario['style']}">
                    {scenario['icon']}
                </div>
                <h3>{name}</h3>
                <p>{scenario['description']}</p>
                <div class="service-arrow">→</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            f"Explore {name}",
            key=f"scenario_{name}",
            use_container_width=True,
        ):
            st.session_state.pending_query = scenario["query"]
            st.rerun()


# ==========================================================
# 9. Conversation history
# ==========================================================
if st.session_state.messages:
    st.markdown("---")
    st.markdown(
        '<div class="section-title">Your conversation</div>',
        unsafe_allow_html=True,
    )

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            details = message.get("details")

            if details:
                with st.expander("View response details"):
                    st.json(details, expanded=False)


# ==========================================================
# 10. Suggested questions
# ==========================================================
#st.markdown(
#    '<div class="suggestion-label">QUICK QUESTIONS</div>',
#    unsafe_allow_html=True,
#)
#
#suggestions = [
#    ("◉  Account & Miles", SCENARIOS["Missing Miles"]["query"]),
#    ("♕  Tier Upgrades", SCENARIOS["Tier Upgrades"]["query"]),
#    ("🎁  Reward flight", SCENARIOS["Reward Bookings"]["query"]),
#    ("✈  Partner airlines", SCENARIOS["Partner Airlines"]["query"]),
#]

#suggestion_columns = st.columns(4, gap="small")

#for column, (label, query) in zip(suggestion_columns, suggestions):
#    with column:
#        if st.button(label, key=f"quick_{label}", use_container_width=True):
#            st.session_state.pending_query = query
#            st.rerun()


# ==========================================================
# 11. Chat input and agent execution
# ==========================================================
user_query = st.chat_input(
    "Ask me anything about your airline loyalty programme..."
)

# A service card or sidebar selection takes priority over empty chat input.
if st.session_state.pending_query:
    query_to_process = st.session_state.pending_query
    st.session_state.pending_query = None
else:
    query_to_process = user_query


if query_to_process:
    st.session_state.messages.append(
        {"role": "user", "content": query_to_process}
    )

    with st.chat_message("user"):
        st.markdown(query_to_process)

    with st.chat_message("assistant"):
        if graph is None:
            error_message = (
                "The assistant could not initialise. "
                "Please check the application logs and agent configuration."
            )
            st.error(error_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "details": {
                        "initialisation_error": agent_initialisation_error
                    },
                }
            )
        else:
            try:
                with st.spinner(
                    "Checking your enquiry and preparing a response..."
                ):
                    # Preserve your existing LangGraph invocation.
                    result = graph.invoke({"query": query_to_process})

                answer = result.get(
                    "response",
                    "I could not generate a response. Please try again.",
                )

                if not isinstance(answer, str):
                    answer = str(answer)

                st.markdown(answer)

                # Keep technical details out of the main customer interface.
                # They remain available for research and evaluation.
                detail_keys = [
                    "intent",
                    "member_id",
                    "validation_status",
                    "escalation_required",
                    "escalation_reason",
                    "trace",
                    "tool_results",
                ]

                details = {
                    key: result[key]
                    for key in detail_keys
                    if key in result
                }

                if details:
                    with st.expander("View response details"):
                        st.json(details, expanded=False)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "details": details,
                    }
                )

            except Exception as exc:
                error_message = (
                    "I'm sorry, but I couldn't process your enquiry "
                    "at this time. Please try again. If the issue persists, "
                    "contact customer support."
                )

                st.error(error_message)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                        "details": {
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        },
                    }
                )

    # Display the newly generated response in the normal chat history
    # on the next Streamlit rerun.
    st.rerun()


# ==========================================================
# 12. Footer
# ==========================================================
#st.markdown(
    #"""
    #<div class="page-note">
    #    AI-assisted loyalty support · Responses are subject to
    #    programme rules and account verification.
    #</div>
    #""",
    #unsafe_allow_html=True,
#)

import streamlit as st

from agent.graph import build_graph


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Airline Loyalty AI Assistant",
    page_icon="✈️",
    layout="wide",
)


# ============================================================
# APPLICATION TITLE
# ============================================================

st.title(
    "✈️ Airline Loyalty AI Customer Service Assistant"
)

st.write(
    """
    An Agentic AI research prototype for airline loyalty
    customer-service enquiries.

    The assistant supports:
    - Missing Miles
    - Tier Upgrades
    - Reward Bookings
    - Family Account Queries
    - Partner Airline Questions
    """
)


# ============================================================
# INITIALISE GRAPH
# ============================================================

@st.cache_resource
def get_agent_graph():

    return build_graph()


graph = get_agent_graph()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Prototype Information")

    st.write(
        """
        **Architecture**

        Streamlit → LangGraph → GPT

        Agent tools:
        - RAG / ChromaDB
        - SQLite
        - Python tools
        - Validation
        - Human escalation
        """
    )

    st.divider()

    st.subheader("Supported Scenarios")

    st.write("1. Missing Miles")
    st.write("2. Tier Upgrades")
    st.write("3. Reward Bookings")
    st.write("4. Family Accounts")
    st.write("5. Partner Airlines")

    st.divider()

    st.caption(
        "Research prototype using synthetic member data."
    )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# ============================================================
# DISPLAY PREVIOUS MESSAGES
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_query = st.chat_input(
    "Enter your airline loyalty enquiry..."
)


# ============================================================
# PROCESS USER QUERY
# ============================================================

if user_query:

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            user_query
        )

    # --------------------------------------------------------
    # Run agent
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Analysing your request..."
        ):

            try:

                result = graph.invoke(
                    {
                        "query": user_query
                    }
                )

                response = result.get(
                    "response",
                    "I was unable to generate a response."
                )

                st.markdown(
                    response
                )

                # ------------------------------------------------
                # Store assistant response
                # ------------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

                # ------------------------------------------------
                # Trace information
                # ------------------------------------------------

                with st.expander(
                    "View Agent Trace"
                ):

                    st.write(
                        "Intent:",
                        result.get(
                            "intent"
                        )
                    )

                    st.write(
                        "Member ID:",
                        result.get(
                            "member_id"
                        )
                    )

                    st.write(
                        "Validation:",
                        result.get(
                            "validation_status"
                        )
                    )

                    st.write(
                        "Escalation Required:",
                        result.get(
                            "escalation_required"
                        )
                    )

                    if result.get(
                        "escalation_reason"
                    ):

                        st.write(
                            "Escalation Reason:",
                            result.get(
                                "escalation_reason"
                            )
                        )

                    st.write(
                        "Trace:"
                    )

                    for item in result.get(
                        "trace",
                        []
                    ):

                        st.write(
                            f"• {item}"
                        )

                    # --------------------------------------------
                    # Tool results
                    # --------------------------------------------

                    tool_results = result.get(
                        "tool_results",
                        {}
                    )

                    if tool_results:

                        st.write(
                            "Tool Results:"
                        )

                        st.json(
                            tool_results
                        )

            except Exception as error:

                error_message = (
                    "An error occurred while "
                    "processing the request."
                )

                st.error(
                    error_message
                )

                st.exception(
                    error
                )
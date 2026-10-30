"""Baseline airline loyalty assistant: Gemini + RAG, without agent tools."""
import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

st.set_page_config(page_title="Airline Loyalty Baseline Assistant", page_icon="✈️", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=False)

from rag.retrieve import retrieve_knowledge

GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

BASELINE_SYSTEM_PROMPT = """You are a customer service assistant for an airline loyalty programme.
You operate as a baseline LLM + Retrieval-Augmented Generation (RAG) system.
Answer customer questions using the retrieved knowledge base.

Instructions:
1. Use retrieved knowledge as your primary source.
2. Do not invent policies, eligibility conditions, account details, transaction statuses, or programme benefits.
3. If the retrieved information is insufficient, explain the limitation.
4. Do not claim to access or modify actual customer loyalty accounts.
5. Do not claim to execute bookings or account changes.
6. Do not claim to have contacted a human agent or created a support case.
7. For member-specific questions, explain that this baseline cannot directly access member records.
8. Distinguish general policy information from individual account results.
9. Provide clear, concise, professional responses.
10. Identify relevant source documents where possible.

This is a baseline retrieval-based assistant, not an autonomous agent.
Do not claim to perform multi-step tool execution."""


@st.cache_resource
def get_gemini_llm(model_name: str):
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key missing. Set GOOGLE_API_KEY in the project .env file or Streamlit Cloud secrets.")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0,
    )


def get_retrieved_context(query: str):
    """Use the same RAG retrieval as the prototype; no member/tool lookups."""
    documents = retrieve_knowledge(query, k=3)
    context_parts = []
    source_names = []
    for index, document in enumerate(documents, start=1):
        if hasattr(document, "page_content"):
            content = document.page_content
            metadata = getattr(document, "metadata", {}) or {}
        elif isinstance(document, dict):
            content = document.get("page_content") or document.get("content") or document.get("text") or ""
            metadata = document.get("metadata", {}) or {}
        else:
            content = str(document)
            metadata = {}
        source = metadata.get("source") or metadata.get("topic") or f"Retrieved document {index}"
        if content and content.strip():
            context_parts.append(f"[Source {index}: {source}]\n{content}")
            source_names.append(str(source))
    return "\n\n".join(context_parts), source_names


def generate_baseline_response(query: str, context: str) -> str:
    """Generate a response with Gemini and retrieved policy text only."""
    llm = get_gemini_llm(GOOGLE_MODEL)
    if context.strip():
        user_prompt = (
            f"CUSTOMER QUESTION:\n{query}\n\nRETRIEVED KNOWLEDGE:\n{context}\n\n"
            "Answer using the retrieved knowledge. If insufficient, explain the limitation. "
            "Do not invent policies or member-specific information."
        )
    else:
        user_prompt = (
            f"CUSTOMER QUESTION:\n{query}\n\n"
            "No relevant knowledge-base documents were retrieved. Explain that available "
            "knowledge is insufficient and do not invent an answer."
        )
    result = llm.invoke([
        SystemMessage(content=BASELINE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    content = result.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part if isinstance(part, str) else part.get("text", "")
                         for part in content if isinstance(part, (str, dict))).strip()
    return str(content or "")


st.title("✈️ Airline Loyalty Customer Service Assistant")
st.subheader("Baseline System — Gemini + RAG")
st.info(
    "This baseline application answers general loyalty-programme questions using Gemini "
    "and retrieved knowledge-base documents. It does not execute account-specific "
    "transactions or autonomous tasks."
)

with st.sidebar:
    st.header("About this system")
    st.markdown("""
**Baseline architecture**

1. Customer submits a question.
2. ChromaDB retrieves relevant knowledge.
3. Gemini generates a response using retrieved context.
4. The application displays the answer and source documents.

**Not included**
- LangGraph orchestration
- Python agent tools
- Direct SQLite member lookup
- Autonomous task execution
- Automated escalation records
""")
    st.divider()
    st.caption(f"Model: {GOOGLE_MODEL}")
    st.caption("Architecture: Gemini + RAG")

if "baseline_messages" not in st.session_state:
    st.session_state.baseline_messages = []
if "baseline_traces" not in st.session_state:
    st.session_state.baseline_traces = []

for message in st.session_state.baseline_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("Retrieved knowledge sources"):
                for source in message["sources"]:
                    st.write(f"- {source}")

user_query = st.chat_input("Ask a question about airline loyalty services...")
if user_query:
    st.session_state.baseline_messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        start_time = time.perf_counter()
        try:
            with st.spinner("Retrieving knowledge and generating response..."):
                retrieved_context, sources = get_retrieved_context(user_query)
                answer = generate_baseline_response(user_query, retrieved_context)
            elapsed_time = time.perf_counter() - start_time
            response_placeholder.markdown(answer)
            st.caption(f"Response time: {elapsed_time:.2f} seconds")
            if sources:
                with st.expander("Retrieved knowledge sources"):
                    for source in sources:
                        st.write(f"- {source}")
            else:
                st.warning("No knowledge-base sources were retrieved.")
            st.session_state.baseline_messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
            st.session_state.baseline_traces.append({
                "query": user_query,
                "sources": sources,
                "response": answer,
                "response_time_seconds": round(elapsed_time, 3),
                "model": GOOGLE_MODEL,
            })
        except Exception as error:
            # Avoid displaying exception text directly: API errors can contain credentials.
            response_placeholder.error(
                "Unable to process this enquiry. Check the application logs and API configuration."
            )
            st.session_state.baseline_messages.append({
                "role": "assistant",
                "content": "Unable to process this enquiry. Please try again.",
                "sources": [],
            })
            st.session_state.baseline_traces.append({
                "query": user_query,
                "status": "ERROR",
                "error_type": type(error).__name__,
                "response_time_seconds": round(time.perf_counter() - start_time, 3),
                "model": GOOGLE_MODEL,
            })

with st.expander("Baseline evaluation trace"):
    st.write("The trace records queries, retrieved sources, responses, model and response times for this session.")
    if st.session_state.baseline_traces:
        st.json(st.session_state.baseline_traces)
    else:
        st.caption("No queries have been processed in this session.")
    if st.button("Clear conversation and trace"):
        st.session_state.baseline_messages = []
        st.session_state.baseline_traces = []
        st.rerun()

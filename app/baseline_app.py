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



# Customer-facing presentation only; Gemini + RAG backend is unchanged.
st.markdown("""
<style>
:root {--navy:#102e58;--blue:#2677d9;--muted:#667c99;}
.stApp {background:#f8fbff;color:#18365a;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#102f59,#092448);}
[data-testid="stSidebar"] * {color:#f7fbff;}
[data-testid="stSidebar"] .stButton button {background:transparent;color:#fff;border:1px solid transparent;text-align:left;width:100%;border-radius:10px;}
[data-testid="stSidebar"] .stButton button:hover {background:#254b7b;border-color:#47678e;}
.brand {font-size:24px;font-weight:800;padding:12px 0 24px;border-bottom:1px solid #55708d;}
.brand small {display:block;font-size:12px;font-weight:400;color:#c3d5ec;}
.hero {padding:35px 32px;border-radius:20px;background:linear-gradient(110deg,#fff 48%,#e7f2ff);border:1px solid #e0eaf7;margin-bottom:28px;}
.hero h1 {font-size:clamp(27px,3vw,39px);line-height:1.2;color:#102f59;margin:8px 0 14px;font-weight:800;}
.hero p {color:#647b99;font-size:15px;}
.eyebrow {font-size:12px;color:#2373ca;letter-spacing:1.4px;font-weight:700;}
.section {font-size:22px;font-weight:750;color:#102f59;margin:10px 0 4px;}
.section-sub {font-size:13px;color:#7185a0;margin-bottom:16px;}
[data-testid="stChatMessage"] {background:#fff;border:1px solid #e5edf8;border-radius:14px;padding:14px;}
[data-testid="stChatInput"] {border:1px solid #d8e6f7;border-radius:14px;background:#fff;}
[data-testid="stMainBlockContainer"] {padding-top:2.5rem;}
.footer-note {text-align:center;color:#8595aa;font-size:11px;margin:28px 0;}
</style>
""", unsafe_allow_html=True)

if "baseline_messages" not in st.session_state:
    st.session_state.baseline_messages = []
if "baseline_traces" not in st.session_state:
    st.session_state.baseline_traces = []
if "baseline_pending" not in st.session_state:
    st.session_state.baseline_pending = None

with st.sidebar:
    st.markdown(
        '<div class="brand">✈ Airline Loyalty<small>Customer Service Assistant</small></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Welcome")
    st.write(
        "Ask questions about airline loyalty programme policies, "
        "miles, rewards, membership tiers and partner benefits."
    )
    st.markdown("### What this assistant can do")
    st.write(
        "Provide general guidance based on available loyalty programme "
        "knowledge and policy documents."
    )
    st.markdown("### Important information")
    st.caption(
        "This research demonstration provides information only. "
        "It cannot access member accounts, confirm personal balances, "
        "make bookings or change account details."
    )
    st.divider()
    if st.button("↺  New conversation", use_container_width=True):
        st.session_state.baseline_messages = []
        st.session_state.baseline_traces = []
        st.session_state.baseline_pending = None
        st.rerun()

st.markdown("""<div class="hero"><div class="eyebrow">YOUR LOYALTY JOURNEY, MADE EASIER</div>
<h1>✈ Airline Loyalty AI<br>Customer Service Assistant</h1>
<p>Welcome! Ask about loyalty programme policies, rewards, tier benefits and more.</p></div>""", unsafe_allow_html=True)
st.markdown(
    '<div class="section">Ask a loyalty programme question</div>'
    '<div class="section-sub">Enter your question in the chat box below to get general programme guidance.</div>',
    unsafe_allow_html=True,
)

if st.session_state.baseline_messages:
    st.markdown("### Your conversation")
for message in st.session_state.baseline_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if "response_time_seconds" in message:
                st.caption(f"Response time: {message['response_time_seconds']:.2f} seconds")
            with st.expander("Knowledge sources"):
                if message.get("sources"):
                    for source in message["sources"]:
                        st.write(f"- {source}")
                else:
                    st.caption("No knowledge-base sources were retrieved.")

user_query = st.chat_input("Ask me anything about your airline loyalty programme...")
if st.session_state.baseline_pending:
    user_query = st.session_state.baseline_pending
    st.session_state.baseline_pending = None

if user_query:
    st.session_state.baseline_messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)
    with st.chat_message("assistant"):
        start_time = time.perf_counter()
        try:
            with st.spinner("Finding relevant loyalty programme information..."):
                retrieved_context, sources = get_retrieved_context(user_query)
                answer = generate_baseline_response(user_query, retrieved_context)
            elapsed_time = time.perf_counter() - start_time
            st.markdown(answer)
            st.caption(f"Response time: {elapsed_time:.2f} seconds")
            with st.expander("Knowledge sources"):
                if sources:
                    for source in sources:
                        st.write(f"- {source}")
                else:
                    st.caption("No knowledge-base sources were retrieved.")
            st.session_state.baseline_messages.append({"role":"assistant", "content":answer, "sources":sources, "response_time_seconds":elapsed_time})
            st.session_state.baseline_traces.append({"query":user_query,"sources":sources,"response":answer,"response_time_seconds":round(elapsed_time,3),"model":GOOGLE_MODEL})
        except Exception as error:
            # Do not expose provider exceptions or credentials to the UI.
            message = "Unable to process this enquiry. Please try again."
            st.error(message)
            st.session_state.baseline_messages.append({"role":"assistant","content":message,"sources":[]})
            st.session_state.baseline_traces.append({"query":user_query,"status":"ERROR","error_type":type(error).__name__,"response_time_seconds":round(time.perf_counter()-start_time,3),"model":GOOGLE_MODEL})
    st.rerun()

with st.expander("Research evaluation details"):
    st.caption("Session-only evaluation trace; no agent tools or account-specific actions are performed.")
    if st.session_state.baseline_traces:
        st.json(st.session_state.baseline_traces)
    else:
        st.caption("No enquiries processed yet.")
    if st.button("Clear conversation and evaluation trace"):
        st.session_state.baseline_messages = []
        st.session_state.baseline_traces = []
        st.rerun()
st.markdown('<div class="footer-note">Research demonstration using simulated loyalty programme knowledge. No live customer account access.</div>', unsafe_allow_html=True)

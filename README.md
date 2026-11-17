# AI Airline Loyalty Agent

An Agentic AI customer service assistant for airline loyalty programme enquiries, developed as part of an MSc Artificial Intelligence research project (University of London Metropolitan). The system is compared against a baseline LLM + RAG assistant.

> **Note:** This is a research prototype. It uses synthetic data only and is not connected to any production loyalty system.

## Key features
- Agentic workflow orchestrated with LangGraph
- RAG over a loyalty knowledge base for grounded answers
- Controlled Python tools querying a synthetic member database
- Response validation and escalation to a human agent for unsupported or sensitive requests
- Streamlit user interface

## Technology stack
| Component | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Orchestration | LangGraph, LangChain Google Generative AI |
| Embeddings | gemini-embedding-001 |
| Vector database | ChromaDB |
| Structured database | SQLite |
| User interface | Streamlit |

## Project structure
- `agent/` – agent logic and workflow
- `app/` – Streamlit application
- `rag/` – retrieval pipeline
- `tools/` – Python tools used by the agent
- `knowledge_base/raw/` – source loyalty documents
- `data/` – synthetic member and transaction data
- `evaluation/` – evaluation test cases and results
- `logs/` – execution logs
- `test_*.py` – test scripts

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set your Gemini API key as an environment variable (or in Streamlit secrets):
   `GOOGLE_API_KEY=your_key_here`
3. Run the app: `streamlit run app/<main_file>.py`

## Evaluation
The prototype was evaluated using 100 test cases across 5 customer service scenarios, with 3 repeated runs per case for each system (600 executions in total).

## Security
Never commit API keys. Credentials are read from environment variables or Streamlit secrets.

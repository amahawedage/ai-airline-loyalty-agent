"""Evaluate GPT+RAG baseline. Run from project root:
python evaluation\evaluate_baseline.py
"""
import os, sys, csv, time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
load_dotenv(ROOT/".env")
MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini").strip()
if not MODEL or MODEL=="gpt-6": MODEL="gpt-5-mini"
from rag.retrieve import retrieve_knowledge

INPUT=ROOT/"evaluation"/"test_cases.csv"
OUTPUT=ROOT/"evaluation"/"baseline_results.csv"
SYSTEM="""You are a customer service assistant for an airline loyalty programme.
This is a baseline GPT+RAG system, not an autonomous agent. Use retrieved
knowledge as the primary source. Do not invent policies, eligibility, account
details or benefits. Do not claim to access or modify actual accounts, execute
bookings or create support cases. If evidence is insufficient, say so clearly.
"""

def retrieve_context(query):
    docs=retrieve_knowledge(query,k=3); chunks=[]; sources=[]
    for i,doc in enumerate(docs,1):
        if hasattr(doc,"page_content"):
            content=doc.page_content; meta=getattr(doc,"metadata",{}) or {}
        elif isinstance(doc,dict):
            content=doc.get("page_content") or doc.get("content") or doc.get("text") or ""
            meta=doc.get("metadata",{}) or {}
        else: content=str(doc); meta={}
        source=meta.get("source") or meta.get("topic") or f"Retrieved document {i}"
        if content and content.strip():
            chunks.append(f"[Source {i}: {source}]\\n{content}"); sources.append(str(source))
    return "\\n\\n".join(chunks), "; ".join(sources)

def main():
    if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is missing in project .env.")
    with INPUT.open(encoding="utf-8-sig",newline="") as f: tests=list(csv.DictReader(f))
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")); results=[]
    for i,t in enumerate(tests,1):
        start=time.perf_counter(); status="success"; error=""; answer=""; sources=""
        try:
            context,sources=retrieve_context(t["question"])
            prompt=f"QUESTION:\\n{t['question']}\\n\\nRETRIEVED KNOWLEDGE:\\n{context or 'No relevant documents retrieved.'}\\n\\nAnswer only from the evidence. State limitations where necessary."
            r=client.chat.completions.create(model=MODEL,messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}])
            answer=r.choices[0].message.content or ""
        except Exception as e: status="error"; error=str(e)
        elapsed=round(time.perf_counter()-start,3)
        results.append({**t,"system":"baseline_gpt_rag","model":MODEL,"actual_response":answer,"retrieved_sources":sources,"response_time_seconds":elapsed,"run_status":status,"error":error})
        print(f"[{i}/{len(tests)}] {t['test_case_id']} {status} {elapsed:.2f}s")
    with OUTPUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    print(f"Saved results: {OUTPUT}")
if __name__=="__main__": main()

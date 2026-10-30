"""Evaluate LangGraph agentic prototype. Run from project root:
python evaluation\evaluate_prototype.py
"""
import sys,csv,time
from pathlib import Path
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
load_dotenv(ROOT/".env")
from agent.graph import build_graph

INPUT=ROOT/"evaluation"/"test_cases.csv"
OUTPUT=ROOT/"evaluation"/"prototype_results.csv"

def make_initial_state(question):
    # If agent/state.py defines a different required schema, align this dict to it.
    return {"query":question,"intent":"","member_id":None,"transaction_id":None,
            "retrieved_context":"","sources":[],"tool_results":{},
            "validation_status":"","validation_message":"",
            "escalation_required":False,"escalation_reason":"",
            "response":"","trace":[]}

def main():
    with INPUT.open(encoding="utf-8-sig",newline="") as f: tests=list(csv.DictReader(f))
    graph=build_graph(); results=[]
    for i,t in enumerate(tests,1):
        start=time.perf_counter(); status="success"; error=""
        answer=sources=intent=tool_results=validation=trace=""; escalation=""
        try:
            out=graph.invoke(make_initial_state(t["question"]))
            answer=str(out.get("response") or "")
            src=out.get("sources") or out.get("retrieved_context") or ""
            sources="; ".join(map(str,src)) if isinstance(src,(list,tuple,set)) else str(src)
            intent=str(out.get("intent") or "")
            tool_results=str(out.get("tool_results") or "")
            validation=str(out.get("validation_status") or "")
            trace=str(out.get("trace") or "")
            escalation=str(out.get("escalation_required",""))
        except Exception as e: status="error"; error=str(e)
        elapsed=round(time.perf_counter()-start,3)
        results.append({**t,"system":"agentic_prototype","actual_response":answer,
            "retrieved_sources_or_context":sources,"intent":intent,"tool_results":tool_results,
            "validation_status":validation,"escalation_required":escalation,"trace":trace,
            "response_time_seconds":elapsed,"run_status":status,"error":error})
        print(f"[{i}/{len(tests)}] {t['test_case_id']} {status} {elapsed:.2f}s")
    with OUTPUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0].keys())); w.writeheader(); w.writerows(results)
    print(f"Saved results: {OUTPUT}")
if __name__=="__main__": main()

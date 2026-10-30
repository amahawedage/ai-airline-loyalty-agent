r"""Evaluate the LangGraph agentic prototype.

Run from the project root:
    python evaluation\evaluate_prototype.py
"""

import csv
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

INPUT = ROOT / "evaluation" / "test_cases.csv"
OUTPUT = ROOT / "evaluation" / "prototype_results.csv"


def make_initial_state(question):
    """Initial graph state; adapt only if agent/state.py requires different keys."""
    return {
        "query": question,
        "intent": "",
        "member_id": None,
        "transaction_id": None,
        "retrieved_context": "",
        "sources": [],
        "tool_results": {},
        "validation_status": "",
        "validation_message": "",
        "escalation_required": False,
        "escalation_reason": "",
        "response": "",
        "trace": [],
    }


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value if not isinstance(value, set) else sorted(value), ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(f"Test cases not found: {INPUT}")

    with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        required = {"test_case_id", "question"}
        missing = required - set(fieldnames)
        if missing:
            raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")
        tests = list(reader)

    if not tests:
        raise ValueError(f"No test cases found in {INPUT}")

    try:
        from agent.graph import build_graph
    except ModuleNotFoundError as exc:
        if exc.name == "langgraph":
            raise RuntimeError(
                "LangGraph is not installed in the active Python environment. "
                "Activate .venv and run: python -m pip install langgraph"
            ) from exc
        raise

    graph = build_graph()
    results = []
    for i, test in enumerate(tests, 1):
        start = time.perf_counter()
        status, error = "success", ""
        answer = sources = intent = tool_results = validation = trace = escalation = ""
        try:
            output = graph.invoke(make_initial_state(test["question"]))
            if not isinstance(output, dict):
                raise TypeError(f"Expected graph output to be a dictionary, got {type(output).__name__}")
            answer = as_text(output.get("response"))
            source_value = output.get("sources") or output.get("retrieved_context")
            sources = "; ".join(map(str, source_value)) if isinstance(source_value, (list, tuple, set)) else as_text(source_value)
            intent = as_text(output.get("intent"))
            tool_results = as_text(output.get("tool_results"))
            validation = as_text(output.get("validation_status"))
            trace = as_text(output.get("trace"))
            escalation = as_text(output.get("escalation_required"))
        except Exception as exc:
            status, error = "error", f"{type(exc).__name__}: {exc}"

        elapsed = round(time.perf_counter() - start, 3)
        results.append({
            **test,
            "system": "agentic_prototype",
            "actual_response": answer,
            "retrieved_sources_or_context": sources,
            "intent": intent,
            "tool_results": tool_results,
            "validation_status": validation,
            "escalation_required": escalation,
            "trace": trace,
            "response_time_seconds": elapsed,
            "run_status": status,
            "error": error,
        })
        print(f"[{i}/{len(tests)}] {test['test_case_id']} {status} {elapsed:.2f}s")
        if error:
            print(f"  {error}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved results: {OUTPUT}")


if __name__ == "__main__":
    main()

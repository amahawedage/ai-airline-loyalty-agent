r"""Evaluate the LangGraph agent, then manually review output quality.

From the project root:
    python evaluation\evaluate_prototype.py
    python evaluation\evaluate_prototype.py --score-existing

Fill accuracy_score (0/1), task_completion_score (0/1),
relevance_score (1-5), hallucination_or_error (0/1) in the results CSV.
Escalation appropriateness is inferred ONLY for explicit expected/actual flags;
review it manually for policy-sensitive cases. --score-existing never calls the LLM.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evaluation_metrics import (SCORE_FIELDS, read_csv, write_results_and_summary)

INPUT = ROOT / 'evaluation' / 'test_cases.csv'
OUTPUT = ROOT / 'evaluation' / 'prototype_results.csv'
SUMMARY = ROOT / 'evaluation' / 'prototype_evaluation_summary.csv'
OUTPUT_FIELDS = ('system', 'actual_response', 'retrieved_sources_or_context',
                 'intent', 'tool_results', 'validation_status',
                 'escalation_required', 'trace', 'response_time_seconds',
                 'run_status', 'error')


def as_text(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value,
                          ensure_ascii=False, default=str)
    return str(value)


def initial_state(question):
    # Each test is independent: no conversation context is inherited.
    return {'query': question, 'intent': '', 'member_id': '',
            'transaction_id': '', 'retrieved_context': [],
            'retrieved_sources': [], 'tool_results': {},
            'validation_status': '', 'validation_message': '',
            'escalation_required': False, 'escalation_reason': '',
            'response': '', 'trace': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-existing', action='store_true',
                        help='Recalculate scores without running the model')
    args = parser.parse_args()
    if args.score_existing:
        rows, fields = read_csv(OUTPUT)
    else:
        tests, fields = read_csv(INPUT)
        missing = {'test_case_id', 'question'} - set(fields)
        if missing:
            raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
        ids = [t['test_case_id'] for t in tests]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate test_case_id values in test_cases.csv')
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
        from agent.graph import build_graph
        graph = build_graph()
        rows = []
        for i, test in enumerate(tests, 1):
            row = dict(test)
            for field in SCORE_FIELDS:
                row[field] = ''  # Old manual scores must never transfer to new answers.
            row.update(system='agentic_prototype', actual_response='',
                       retrieved_sources_or_context='', intent='', tool_results='',
                       validation_status='', escalation_required='', trace='',
                       response_time_seconds='', run_status='success', error='')
            start = time.perf_counter()
            try:
                result = graph.invoke(initial_state(test['question']))
                if not isinstance(result, dict):
                    raise TypeError('Graph output must be a dictionary')
                sources = result.get('retrieved_sources') or result.get('retrieved_context') or []
                row.update(actual_response=as_text(result.get('response')),
                           retrieved_sources_or_context=as_text(sources),
                           intent=as_text(result.get('intent')),
                           tool_results=as_text(result.get('tool_results')),
                           validation_status=as_text(result.get('validation_status')),
                           escalation_required=as_text(result.get('escalation_required')),
                           trace=as_text(result.get('trace')))
            except Exception as exc:
                row['run_status'] = 'error'
                row['error'] = f'{type(exc).__name__}: {exc}'
            row['response_time_seconds'] = round(time.perf_counter() - start, 3)
            rows.append(row)
            print(f'[{i}/{len(tests)}] {test["test_case_id"]}: {row["run_status"]} ({row["response_time_seconds"]}s)', flush=True)
    missing_reviews = write_results_and_summary(OUTPUT, SUMMARY, rows,
                                                list(fields) + list(OUTPUT_FIELDS),
                                                'agentic_prototype')
    print(f'Saved: {OUTPUT}\nSaved: {SUMMARY}')
    print(f'Cases requiring review: {missing_reviews}/{len(rows)}')


if __name__ == '__main__':
    main()

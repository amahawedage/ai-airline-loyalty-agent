r"""Evaluate the LangGraph prototype and produce auditable evaluation results.

From the project root:
    python evaluation\evaluate_prototype_new.py
    python evaluation\evaluate_prototype_new.py --score-existing

Manual scoring: fill accuracy_score (0/1), task_completion_score (0/1),
relevance_score (1-5), hallucination_or_error (0/1) and optionally
escalation_appropriate (0/1) in prototype_results.csv. Then run --score-existing.
Unknown subjective scores remain blank, never assumed correct.
"""
import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
INPUT = ROOT / 'evaluation' / 'test_cases.csv'
OUTPUT = ROOT / 'evaluation' / 'prototype_results.csv'
SUMMARY = ROOT / 'evaluation' / 'prototype_evaluation_summary.csv'
SCORE_FIELDS = ('accuracy_score', 'task_completion_score', 'relevance_score',
                'hallucination_or_error', 'escalation_appropriate')
EXTRA_FIELDS = ('system', 'actual_response', 'retrieved_sources_or_context', 'intent',
                'tool_results', 'validation_status', 'escalation_required', 'trace',
                'response_time_seconds', 'run_status', 'error',
                'response_accuracy_percent', 'task_completion_percent',
                'relevance_and_completeness', 'hallucination_error_percent',
                'escalation_appropriateness_percent', 'review_status')


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f'CSV not found: {path}')
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f'CSV has no header: {path}')
        rows = list(reader)
        if not rows:
            raise ValueError(f'CSV contains no rows: {path}')
        return rows, reader.fieldnames


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def as_text(value):
    if value is None:
        return ''
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(sorted(value) if isinstance(value, set) else value,
                          ensure_ascii=False, default=str)
    return str(value)


def make_initial_state(question):
    return {'query': question, 'intent': '', 'member_id': None,
            'transaction_id': None, 'retrieved_context': '', 'sources': [],
            'tool_results': {}, 'validation_status': '', 'validation_message': '',
            'escalation_required': False, 'escalation_reason': '',
            'response': '', 'trace': []}


def binary(value):
    s = str(value).strip().lower()
    if s in ('1', 'yes', 'true', 'pass', 'correct'):
        return 1
    if s in ('0', 'no', 'false', 'fail', 'incorrect'):
        return 0
    return None


def expected_escalation(value):
    s = str(value).strip().lower().replace(' ', '_').replace('-', '_')
    if s in ('required', 'escalate', 'yes', 'true', '1'):
        return True
    if s in ('not_required', 'not_required.', 'no', 'false', '0'):
        return False
    return None


def actual_escalation(value):
    s = str(value).strip().lower()
    if s in ('true', '1', 'yes'):
        return True
    if s in ('false', '0', 'no'):
        return False
    return None


def score_rows(rows):
    for row in rows:
        # Only infer escalation correctness from explicit expected/actual flags.
        expected = expected_escalation(row.get('expected_escalation', ''))
        actual = actual_escalation(row.get('escalation_required', ''))
        if not str(row.get('escalation_appropriate', '')).strip() and expected is not None and actual is not None and row.get('run_status') == 'success':
            row['escalation_appropriate'] = str(int(expected == actual))
        for source, dest in (('accuracy_score', 'response_accuracy_percent'),
                             ('task_completion_score', 'task_completion_percent'),
                             ('hallucination_or_error', 'hallucination_error_percent'),
                             ('escalation_appropriate', 'escalation_appropriateness_percent')):
            v = binary(row.get(source, ''))
            row[dest] = str(v * 100) if v is not None else ''
        relevance = str(row.get('relevance_score', '')).strip()
        try:
            n = float(relevance)
            row['relevance_and_completeness'] = str(n) if 1 <= n <= 5 else ''
        except ValueError:
            row['relevance_and_completeness'] = ''
        row['review_status'] = ('complete' if all(str(row.get(k, '')).strip() for k in SCORE_FIELDS)
                                else 'manual_review_required')
    return rows


def build_summary(rows):
    summary = []
    def metric(name, values, unit, total):
        summary.append({'metric': name, 'value': round(statistics.mean(values), 3) if values else '',
                        'unit': unit, 'scored_cases': len(values), 'total_cases': total,
                        'note': '' if len(values) == total else 'Partial coverage; unscored cases excluded'})
    total = len(rows)
    for label, field in (('Response accuracy (%)', 'accuracy_score'),
                         ('Task completion (%)', 'task_completion_score'),
                         ('Hallucination/error rate (%)', 'hallucination_or_error'),
                         ('Escalation appropriateness (%)', 'escalation_appropriate')):
        vals = [binary(r.get(field, '')) for r in rows]
        metric(label, [100 * v for v in vals if v is not None], '%', total)
    vals = []
    for r in rows:
        try:
            v = float(r.get('relevance_score', ''))
            if 1 <= v <= 5:
                vals.append(v)
        except (ValueError, TypeError):
            pass
    metric('Relevance and completeness (1-5)', vals, 'score / 5', total)
    times = []
    for r in rows:
        try:
            v = float(r.get('response_time_seconds', ''))
            if v >= 0:
                times.append(v)
        except (ValueError, TypeError):
            pass
    metric('Mean response time (seconds)', times, 'seconds', total)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-existing', action='store_true',
                        help='Recalculate metrics without invoking the agent; preserves manual scores')
    args = parser.parse_args()
    if args.score_existing:
        rows, fields = read_csv(OUTPUT)
    else:
        tests, fields = read_csv(INPUT)
        required = {'test_case_id', 'question'}
        missing = required - set(fields)
        if missing:
            raise ValueError('Missing test case columns: ' + ', '.join(sorted(missing)))
        from dotenv import load_dotenv
        load_dotenv(ROOT / '.env')
        from agent.graph import build_graph
        graph = build_graph()
        # Preserve any previously reviewed scores when rerunning same test IDs.
        old = {}
        if OUTPUT.exists():
            previous, _ = read_csv(OUTPUT)
            old = {r['test_case_id']: r for r in previous}
        rows = []
        for i, test in enumerate(tests, 1):
            case_id = test['test_case_id']
            row = dict(test)
            # Prior scores refer to prior outputs: never carry them to a new agent response.
            for field in SCORE_FIELDS:
                row[field] = ''
            start = time.perf_counter()
            result = {'system': 'agentic_prototype', 'actual_response': '',
                      'retrieved_sources_or_context': '', 'intent': '', 'tool_results': '',
                      'validation_status': '', 'escalation_required': '', 'trace': '',
                      'run_status': 'success', 'error': ''}
            try:
                output = graph.invoke(make_initial_state(test['question']))
                if not isinstance(output, dict):
                    raise TypeError('Agent graph output must be a dictionary')
                source = output.get('sources') or output.get('retrieved_context')
                result.update(actual_response=as_text(output.get('response')),
                              retrieved_sources_or_context='; '.join(map(str, source)) if isinstance(source, (list, tuple, set)) else as_text(source),
                              intent=as_text(output.get('intent')),
                              tool_results=as_text(output.get('tool_results')),
                              validation_status=as_text(output.get('validation_status')),
                              escalation_required=as_text(output.get('escalation_required')),
                              trace=as_text(output.get('trace')))
            except Exception as exc:
                result['run_status'] = 'error'
                result['error'] = f'{type(exc).__name__}: {exc}'
            result['response_time_seconds'] = round(time.perf_counter() - start, 3)
            row.update(result)
            rows.append(row)
            print(f'[{i}/{len(tests)}] {case_id}: {result["run_status"]} ({result["response_time_seconds"]}s)')
    fields = list(dict.fromkeys(list(fields) + list(EXTRA_FIELDS)))
    rows = score_rows(rows)
    write_csv(OUTPUT, rows, fields)
    write_csv(SUMMARY, build_summary(rows), ['metric', 'value', 'unit', 'scored_cases', 'total_cases', 'note'])
    print(f'Saved: {OUTPUT}\nSaved: {SUMMARY}')
    print(f'Cases requiring manual review: {sum(r["review_status"] != "complete" for r in rows)}/{len(rows)}')

if __name__ == '__main__':
    main()

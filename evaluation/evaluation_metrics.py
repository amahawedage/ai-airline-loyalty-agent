"""Shared, auditable scoring for baseline and agentic prototype evaluations.

Human review is required for factual accuracy, completion, relevance and hallucination.
Automatic escalation scoring is only possible when both expected and actual flags
are explicitly available; it is not a substitute for assessing escalation quality.
"""
import csv
import statistics
from pathlib import Path

SCORE_FIELDS = ('accuracy_score', 'task_completion_score', 'relevance_score',
                'hallucination_or_error', 'escalation_appropriate')
DERIVED_FIELDS = ('response_accuracy_percent', 'task_completion_percent',
                  'relevance_and_completeness', 'hallucination_error_percent',
                  'escalation_appropriateness_percent', 'review_status')
SUMMARY_FIELDS = ('metric', 'value', 'unit', 'scored_cases', 'total_cases', 'note')


def read_csv(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'CSV not found: {path}')
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f'CSV has no header: {path}')
        rows = list(reader)
    if not rows:
        raise ValueError(f'CSV contains no rows: {path}')
    return rows, list(reader.fieldnames)


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(fields)), extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def binary(value):
    s = str(value if value is not None else '').strip().lower()
    if s in ('1', 'yes', 'true', 'pass', 'correct'):
        return 1
    if s in ('0', 'no', 'false', 'fail', 'incorrect'):
        return 0
    return None


def expected_escalation(value):
    s = str(value or '').strip().lower().replace(' ', '_').replace('-', '_')
    if s in ('required', 'escalate', 'yes', 'true', '1'):
        return True
    if s in ('not_required', 'no', 'false', '0'):
        return False
    # e.g. 'not_required_unless_policy_requires' cannot be scored automatically.
    return None


def actual_escalation(value):
    s = str(value or '').strip().lower()
    if s in ('true', 'yes', '1'):
        return True
    if s in ('false', 'no', '0'):
        return False
    return None


def number(value, minimum=None, maximum=None):
    try:
        n = float(value)
        if not (n == n and abs(n) != float('inf')):
            return None
        if minimum is not None and n < minimum:
            return None
        if maximum is not None and n > maximum:
            return None
        return n
    except (TypeError, ValueError):
        return None


def score_rows(rows, system):
    for row in rows:
        success = row.get('run_status') == 'success'
        # The baseline cannot perform a human handoff. Do not score a lack of
        # escalation as appropriate/inappropriate unless manually reviewed.
        if system == 'agentic_prototype' and success and not str(row.get('escalation_appropriate', '')).strip():
            expected = expected_escalation(row.get('expected_escalation'))
            actual = actual_escalation(row.get('escalation_required'))
            if expected is not None and actual is not None:
                row['escalation_appropriate'] = str(int(expected == actual))
        for source, dest in (('accuracy_score', 'response_accuracy_percent'),
                             ('task_completion_score', 'task_completion_percent'),
                             ('hallucination_or_error', 'hallucination_error_percent'),
                             ('escalation_appropriate', 'escalation_appropriateness_percent')):
            value = binary(row.get(source))
            row[dest] = str(value * 100) if value is not None else ''
        relevance = number(row.get('relevance_score'), 1, 5)
        row['relevance_and_completeness'] = f'{relevance:g}' if relevance is not None else ''
        required = SCORE_FIELDS if system == 'agentic_prototype' else SCORE_FIELDS[:4]
        row['review_status'] = ('complete' if success and all(
            (binary(row.get(k)) is not None if k != 'relevance_score'
             else number(row.get(k), 1, 5) is not None) for k in required
        ) else 'manual_review_required')
    return rows


def build_summary(rows, system):
    total = len(rows)
    summary = []
    metrics = (
        ('Response accuracy (%)', 'accuracy_score', '%', 100),
        ('Task completion (%)', 'task_completion_score', '%', 100),
        ('Relevance and completeness (1-5)', 'relevance_score', 'score / 5', 1),
        ('Mean response time (seconds)', 'response_time_seconds', 'seconds', 1),
        ('Hallucination/error rate (%)', 'hallucination_or_error', '%', 100),
        ('Escalation appropriateness (%)', 'escalation_appropriate', '%', 100),
    )
    for label, field, unit, multiplier in metrics:
        if system == 'baseline_gpt_rag' and field == 'escalation_appropriate':
            summary.append({'metric': label, 'value': '', 'unit': unit,
                            'scored_cases': 0, 'total_cases': total,
                            'note': 'Not applicable: baseline has no escalation tool; assess separately if desired'})
            continue
        values = []
        for row in rows:
            if row.get('run_status') != 'success':
                continue
            if field == 'relevance_score':
                value = number(row.get(field), 1, 5)
            elif field == 'response_time_seconds':
                value = number(row.get(field), 0)
            else:
                value = binary(row.get(field))
            if value is not None:
                values.append(value * multiplier)
        summary.append({'metric': label,
                        'value': round(statistics.mean(values), 3) if values else '',
                        'unit': unit, 'scored_cases': len(values), 'total_cases': total,
                        'note': '' if len(values) == total else 'Partial coverage; unscored or failed cases excluded'})
    return summary


def write_results_and_summary(output, summary_path, rows, fields, system):
    fields = list(dict.fromkeys(list(fields) + list(SCORE_FIELDS) + list(DERIVED_FIELDS)))
    score_rows(rows, system)
    write_csv(output, rows, fields)
    write_csv(summary_path, build_summary(rows, system), SUMMARY_FIELDS)
    return sum(r['review_status'] != 'complete' for r in rows)

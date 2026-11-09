r"""Evaluate GPT+RAG baseline with the same human-scoring methodology.

From the project root:
    python evaluation\evaluate_baseline.py
    python evaluation\evaluate_baseline.py --score-existing

Baseline has no member database tools or escalation mechanism. Its escalation
appropriateness is reported N/A, not automatically marked correct or incorrect.
"""
import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evaluation_metrics import (SCORE_FIELDS, read_csv, write_results_and_summary)

INPUT = ROOT / 'evaluation' / 'test_cases.csv'
OUTPUT = ROOT / 'evaluation' / 'baseline_results.csv'
SUMMARY = ROOT / 'evaluation' / 'baseline_evaluation_summary.csv'
OUTPUT_FIELDS = ('system', 'model', 'actual_response', 'retrieved_sources_or_context',
                 'response_time_seconds', 'run_status', 'error')
SYSTEM = """You are a customer service assistant for a simulated airline loyalty programme.
This is a baseline LLM+RAG system without access to member databases, business
transaction tools, or human escalation. Use retrieved knowledge as evidence.
Never invent member balances, transaction details, availability, or policies.
If you cannot verify an account-specific answer, say so and recommend the
appropriate next step. Never claim to book flights or create support cases.
"""


def retrieve_context(query):
    from rag.retrieve import retrieve_knowledge
    docs = retrieve_knowledge(query, k=3)
    chunks, sources = [], []
    for i, doc in enumerate(docs, 1):
        content = getattr(doc, 'page_content', '')
        metadata = getattr(doc, 'metadata', {}) or {}
        if isinstance(doc, dict):
            content = doc.get('page_content') or doc.get('content') or doc.get('text') or ''
            metadata = doc.get('metadata') or {}
        if str(content).strip():
            source = metadata.get('source') or metadata.get('topic') or f'Document {i}'
            chunks.append(f'[Source {i}: {source}]\n{content}')
            sources.append(str(source))
    return '\n\n'.join(chunks), '; '.join(sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-existing', action='store_true',
                        help='Recalculate scores without invoking the model')
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
        from openai import OpenAI
        if not os.getenv('GOOGLE_API_KEY'):
            raise RuntimeError('GOOGLE_API_KEY missing in .env')
        model = os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash').strip() or 'gemini-2.5-flash'
        client = OpenAI(api_key=os.getenv('GOOGLE_API_KEY'))
        rows = []
        for i, test in enumerate(tests, 1):
            row = dict(test)
            for field in SCORE_FIELDS:
                row[field] = ''
            row.update(system='baseline_gpt_rag', model=model, actual_response='',
                       retrieved_sources_or_context='', response_time_seconds='',
                       run_status='success', error='')
            start = time.perf_counter()
            try:
                context, sources = retrieve_context(test['question'])
                row['retrieved_sources_or_context'] = sources
                prompt = (f"QUESTION:\n{test['question']}\n\n"
                          f"RETRIEVED KNOWLEDGE:\n{context or 'No relevant documents retrieved.'}\n\n"
                          'Respond only with supported information. If member-specific facts '
                          'cannot be verified, explain the limitation.')
                response = client.chat.completions.create(
                    model=model, messages=[{'role': 'system', 'content': SYSTEM},
                                           {'role': 'user', 'content': prompt}])
                row['actual_response'] = response.choices[0].message.content or ''
            except Exception as exc:
                row['run_status'] = 'error'
                row['error'] = f'{type(exc).__name__}: {exc}'
            row['response_time_seconds'] = round(time.perf_counter() - start, 3)
            rows.append(row)
            print(f'[{i}/{len(tests)}] {test["test_case_id"]}: {row["run_status"]} ({row["response_time_seconds"]}s)', flush=True)
    missing_reviews = write_results_and_summary(OUTPUT, SUMMARY, rows,
                                                list(fields) + list(OUTPUT_FIELDS),
                                                'baseline_gpt_rag')
    print(f'Saved: {OUTPUT}\nSaved: {SUMMARY}')
    print(f'Cases requiring review: {missing_reviews}/{len(rows)}')


if __name__ == '__main__':
    main()

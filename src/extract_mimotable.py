"""
Extract QA pairs from MiMoTable for benchmark evaluation.
Filters to Lookup and Compare operations, extracts short answers from verbose prose.
"""

import json
import os
import re


def extract_short_answer(verbose_answer: str) -> str:
    """Extract a concise answer value from MiMoTable's verbose prose answers.

    MiMoTable answers are full sentences like:
      'the applicant for "Material Name 1" is "Xia Zhu".'
      'Shop A actual sales on April 6 were 5035.3'
      'the machinery name for number "11-1" is "Dry Excavation Shield Tunneling Machine"'

    We extract the key value by looking for quoted strings, "is/are/was/were X" patterns,
    and final numeric values.
    """
    answer = verbose_answer.strip()

    # Look for bold markdown answers: **answer**
    bold = re.findall(r'\*\*(.+?)\*\*', answer)
    if bold:
        # Take the last bold text as the answer
        return bold[-1].strip(".,;: ")

    # Look for "is/are/was/were [value]" patterns with quoted values
    is_quoted = re.findall(r'(?:is|are|was|were)\s+["\u201c](.+?)["\u201d]', answer, re.IGNORECASE)
    if is_quoted:
        return is_quoted[-1].strip(".,;: ")

    # Look for "is/are/was/were [value]" with unquoted short values
    is_pattern = re.findall(r'(?:is|are|was|were)\s+([A-Z][a-zA-Z\s]{1,40}?)(?:\.|,|\s+(?:and|which|if|for|the|in|on|at|to|of))', answer)
    if is_pattern:
        return is_pattern[-1].strip(".,;: ")

    # Look for numbers at end of sentences
    nums = re.findall(r'(\d[\d,]*\.?\d*)\s*(?:yuan|%|dollars|USD|RMB)?', answer)
    if nums:
        return nums[-1].replace(",", "")

    # Look for any quoted strings
    quoted = re.findall(r'["\u201c](.+?)["\u201d]', answer)
    if quoted:
        # Return the last quoted string that looks like a value (not a column name)
        for q in reversed(quoted):
            if len(q) < 80:
                return q.strip(".,;: ")

    # Fall back to first sentence, trimmed
    first_sent = answer.split(".")[0].strip()
    if len(first_sent) < 100:
        return first_sent

    return answer[:100]


def extract_mimotable_questions(corpus_dir: str) -> list[dict]:
    """Extract Lookup and Compare questions from MiMoTable."""
    questions = []
    problems_path = os.path.join(corpus_dir, "data/english/problems.json")

    data = []
    with open(problems_path) as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    target_ops = {"Lookup", "Compare"}
    for item in data:
        ops = set(item.get("meta_operation_list", []))
        # Keep only if ALL operations are Lookup or Compare (no Calculate, Reasoning, etc.)
        if not ops or not ops.issubset(target_ops):
            continue

        # Skip questions with very long answers (likely open-ended)
        if len(item["answer"]) > 500:
            continue

        spreadsheet_paths = item.get("spreadsheet_list", [])
        if not spreadsheet_paths:
            continue

        # Resolve spreadsheet path
        sp_rel = spreadsheet_paths[0].lstrip("./")
        sp_path = os.path.join(corpus_dir, "data/english", sp_rel)
        if not os.path.exists(sp_path):
            continue

        short_answer = extract_short_answer(item["answer"])

        questions.append({
            "workbook": os.path.basename(sp_path),
            "workbook_path": os.path.abspath(sp_path),
            "question": item["question"],
            "answer_resolved": short_answer,
            "answer_verbose": item["answer"],
            "question_type": "+".join(sorted(ops)),
            "difficulty": "Medium" if len(ops) > 1 else "Easy",
            "sheet": "_workbook",
            "meta_operations": item["meta_operation_list"],
        })

    return questions


if __name__ == "__main__":
    corpus_dir = "corpus/mimotable"
    questions = extract_mimotable_questions(corpus_dir)
    print(f"Extracted {len(questions)} Lookup/Compare questions")

    types = {}
    for q in questions:
        types[q["question_type"]] = types.get(q["question_type"], 0) + 1
    print(f"Types: {json.dumps(types, indent=2)}")

    print("\nSamples:")
    for q in questions[:10]:
        print(f"  [{q['question_type']}] Q: {q['question'][:70]}")
        print(f"    Short A: {q['answer_resolved'][:60]}")
        print(f"    Full  A: {q['answer_verbose'][:80]}")
        print()

    with open("data/mimotable_questions.json", "w") as f:
        json.dump(questions, f, indent=2, default=str)
    print(f"Saved to data/mimotable_questions.json")

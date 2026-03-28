"""
Main evaluation harness for SCF benchmarking.
Runs LLM evaluations across multiple spreadsheet formats and collects results.
"""

import json
import os
import sys
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

from converters import FORMATS
from scoring import score_answer, extract_answer_from_response

load_dotenv()

EVAL_PROMPT_TEMPLATE = """You are an expert spreadsheet analyst. You will be given the contents of a spreadsheet workbook in {format_name} format, followed by a question about the data.

Answer the question as precisely as possible. If the answer is a number, give the exact numeric value. If you need to calculate something, show your reasoning briefly, then give a final answer.

IMPORTANT: End your response with a line that starts with "Answer:" followed by your concise final answer (a number, name, yes/no, etc). Do not include units unless specifically asked.

{spreadsheet_content}

Question: {question}"""

# Models to evaluate with
MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
]

# Formats to compare
FORMAT_NAMES = ["scf", "csv", "markdown", "json", "sheetcompressor"]

# Cache directory for converted spreadsheets and LLM responses
CACHE_DIR = "data/cache"
RESPONSE_CACHE_DIR = "data/response_cache"


def get_cache_path(workbook_path: str, fmt: str, max_rows: int) -> str:
    """Get cache path for a converted spreadsheet."""
    key = hashlib.md5(f"{workbook_path}:{fmt}:{max_rows}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.txt")


def get_response_cache_path(prompt_hash: str, model: str) -> str:
    """Get cache path for an LLM response."""
    return os.path.join(RESPONSE_CACHE_DIR, f"{model}_{prompt_hash}.json")


def convert_workbook(workbook_path: str, fmt: str, max_rows: int = 200) -> str:
    """Convert a workbook to the specified format, with caching."""
    cache_path = get_cache_path(workbook_path, fmt, max_rows)
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return f.read()

    converter = FORMATS[fmt]
    result = converter(workbook_path, max_rows_per_sheet=max_rows)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        f.write(result)

    return result


def call_llm(prompt: str, model: str, client: OpenAI) -> tuple[str, dict]:
    """Call the LLM with caching. Returns (response_text, usage_info)."""
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:16]
    cache_path = get_response_cache_path(prompt_hash, model)

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            cached = json.load(f)
        return cached["response"], cached["usage"]

    # Newer models (5.x+) require max_completion_tokens instead of max_tokens
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    if model.startswith("gpt-5") or model.startswith("gpt-4.1") or model.startswith("o"):
        kwargs["max_completion_tokens"] = 2048
    else:
        kwargs["max_tokens"] = 2048
    response = client.chat.completions.create(**kwargs)

    text = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump({"response": text, "usage": usage, "model": model, "prompt_hash": prompt_hash}, f)

    return text, usage


def format_display_name(fmt: str) -> str:
    names = {
        "ream": "Ream",
        "ream_addressed": "Ream-Addressed",
        "scf": "SCF",
        "scf_addressed": "SCF-Addressed",
        "scf_formulas": "SCF-Formulas",
        "csv": "CSV",
        "markdown": "Markdown",
        "markdown_kv": "Markdown-KV",
        "json": "JSON",
        "html": "HTML",
        "xml": "XML",
        "pandas": "Pandas",
        "cell_address_md": "CellAddr-MD",
        "sheetcompressor": "SheetCompressor",
        "reverse_index_values": "ReverseIdx-Values",
        "raw_xlsx": "Raw-XLSX-B64",
        "raw_ooxml": "Raw-OOXML",
    }
    return names.get(fmt, fmt)


def run_single_eval(question: dict, fmt: str, model: str, client: OpenAI, max_rows: int = 200) -> dict:
    """Run a single evaluation: one question, one format, one model."""
    workbook_path = question["workbook_path"]
    converted = convert_workbook(workbook_path, fmt, max_rows)
    token_count = len(converted.split())  # rough word count as proxy

    prompt = EVAL_PROMPT_TEMPLATE.format(
        format_name=format_display_name(fmt),
        spreadsheet_content=converted,
        question=question["question"],
    )

    response_text, usage = call_llm(prompt, model, client)
    extracted_answer = extract_answer_from_response(response_text)
    score_result = score_answer(extracted_answer, question["answer_resolved"])

    return {
        "question_id": f"{question['workbook']}:{question['question'][:50]}",
        "workbook": question["workbook"],
        "question": question["question"],
        "ground_truth": question["answer_resolved"],
        "difficulty": question["difficulty"],
        "reasoning_type": question.get("reasoning_type", question.get("question_type", "")),
        "format": fmt,
        "model": model,
        "predicted_answer": extracted_answer,
        "full_response": response_text,
        "score": score_result,
        "tokens": usage,
        "content_word_count": token_count,
    }


def run_evaluation(
    questions_path: str = "data/frtr_questions_clean.json",
    models: list[str] | None = None,
    formats: list[str] | None = None,
    max_rows: int = 200,
    max_questions: int | None = None,
    parallel: int = 5,
) -> dict:
    """Run the full evaluation suite."""
    models = models or MODELS
    formats = formats or FORMAT_NAMES

    with open(questions_path) as f:
        questions = json.load(f)

    if max_questions:
        questions = questions[:max_questions]

    client = OpenAI()
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(RESPONSE_CACHE_DIR, exist_ok=True)

    total_evals = len(questions) * len(formats) * len(models)
    print(f"Running {total_evals} evaluations: {len(questions)} questions x {len(formats)} formats x {len(models)} models")
    print(f"Models: {models}")
    print(f"Formats: {formats}")
    print()

    results = []
    errors = []

    # Pre-convert all workbooks to all formats (parallelized)
    workbook_paths = list(set(q["workbook_path"] for q in questions))
    print(f"Pre-converting {len(workbook_paths)} workbooks to {len(formats)} formats...")
    for wp in tqdm(workbook_paths, desc="Converting"):
        for fmt in formats:
            try:
                convert_workbook(wp, fmt, max_rows)
            except Exception as e:
                print(f"  ERROR converting {wp} to {fmt}: {e}")

    # Run evaluations
    def run_one(args):
        q, fmt, model = args
        try:
            return run_single_eval(q, fmt, model, client, max_rows)
        except Exception as e:
            return {"error": str(e), "question": q["question"][:50], "format": fmt, "model": model}

    eval_args = [(q, fmt, model) for q in questions for fmt in formats for model in models]

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(run_one, args): args for args in eval_args}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Evaluating"):
            result = future.result()
            if "error" in result:
                errors.append(result)
            else:
                results.append(result)

    # Compute aggregate statistics
    stats = compute_stats(results, models, formats)

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_questions": len(questions),
            "models": models,
            "formats": formats,
            "max_rows_per_sheet": max_rows,
            "total_evaluations": len(results),
            "errors": len(errors),
        },
        "stats": stats,
        "results": results,
        "errors": errors,
    }

    return output


def compute_stats(results: list[dict], models: list[str], formats: list[str]) -> dict:
    """Compute aggregate statistics from results."""
    stats = {}

    for model in models:
        stats[model] = {}
        for fmt in formats:
            fmt_results = [r for r in results if r["model"] == model and r["format"] == fmt]
            if not fmt_results:
                continue

            correct = sum(1 for r in fmt_results if r["score"]["correct"])
            total = len(fmt_results)
            avg_score = sum(r["score"]["score"] for r in fmt_results) / total if total else 0
            avg_tokens = sum(r["tokens"]["total_tokens"] for r in fmt_results) / total if total else 0
            avg_content_words = sum(r["content_word_count"] for r in fmt_results) / total if total else 0

            # By difficulty
            by_difficulty = {}
            for diff in ["Easy", "Medium", "Hard", "Hardest"]:
                diff_results = [r for r in fmt_results if r["difficulty"] == diff]
                if diff_results:
                    diff_correct = sum(1 for r in diff_results if r["score"]["correct"])
                    by_difficulty[diff] = {
                        "accuracy": diff_correct / len(diff_results),
                        "correct": diff_correct,
                        "total": len(diff_results),
                    }

            stats[model][fmt] = {
                "accuracy": correct / total,
                "correct": correct,
                "total": total,
                "avg_score": avg_score,
                "avg_total_tokens": avg_tokens,
                "avg_content_words": avg_content_words,
                "by_difficulty": by_difficulty,
            }

    return stats


def print_summary(output: dict):
    """Print a formatted summary of results."""
    stats = output["stats"]
    meta = output["metadata"]

    print(f"\n{'='*80}")
    print(f"SCF BENCHMARK RESULTS")
    print(f"{'='*80}")
    print(f"Questions: {meta['num_questions']} | Evaluations: {meta['total_evaluations']} | Errors: {meta['errors']}")
    print()

    for model in meta["models"]:
        print(f"\n--- Model: {model} ---")
        print(f"{'Format':<12} {'Accuracy':>10} {'Correct':>10} {'Avg Score':>10} {'Avg Tokens':>12} {'Avg Words':>10}")
        print(f"{'-'*12} {'-'*10} {'-'*10} {'-'*10} {'-'*12} {'-'*10}")

        for fmt in meta["formats"]:
            s = stats.get(model, {}).get(fmt, {})
            if not s:
                continue
            print(f"{fmt:<12} {s['accuracy']:>10.1%} {s['correct']:>7}/{s['total']:<3} {s['avg_score']:>10.3f} {s['avg_total_tokens']:>12.0f} {s['avg_content_words']:>10.0f}")

        # By difficulty breakdown
        print(f"\n  By difficulty:")
        print(f"  {'Format':<12} {'Easy':>10} {'Medium':>10} {'Hard':>10} {'Hardest':>10}")
        for fmt in meta["formats"]:
            s = stats.get(model, {}).get(fmt, {})
            if not s:
                continue
            parts = []
            for diff in ["Easy", "Medium", "Hard", "Hardest"]:
                d = s.get("by_difficulty", {}).get(diff, {})
                if d:
                    parts.append(f"{d['accuracy']:>8.0%}")
                else:
                    parts.append(f"{'N/A':>8}")
            print(f"  {fmt:<12} {'  '.join(parts)}")

    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run SCF benchmark evaluation")
    parser.add_argument("--questions", default="data/frtr_questions_clean.json")
    parser.add_argument("--models", nargs="+", default=MODELS)
    parser.add_argument("--formats", nargs="+", default=FORMAT_NAMES)
    parser.add_argument("--max-rows", type=int, default=200)
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--parallel", type=int, default=5)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    output = run_evaluation(
        questions_path=args.questions,
        models=args.models,
        formats=args.formats,
        max_rows=args.max_rows,
        max_questions=args.max_questions,
        parallel=args.parallel,
    )

    print_summary(output)

    # Save results
    out_path = args.output or f"results/eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"Results saved to {out_path}")

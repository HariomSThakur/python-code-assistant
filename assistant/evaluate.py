"""Compare local generation and the configured model on a small prompt set.

This checks parseable Python and expected function names. It does not execute or
grade the generated programs, so this is a lightweight structural evaluation,
not a measure of functional correctness.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from . import create_app
from .db import get_db
from .generation import generate_code
from .llm import ModelError, ask_model, model_status

ROOT = Path(__file__).resolve().parents[1]
TASK_FILE = ROOT / "evals" / "code_tasks.json"


def python_source(response: str) -> str:
    match = re.search(r"```(?:python|py)?\s*\n?(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else response.strip()


def assess(response: str, expected_function: str) -> dict:
    source = python_source(response)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"syntax_valid": False, "expected_function_found": False}
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    return {"syntax_valid": True, "expected_function_found": expected_function in names}


def summarize(results: list[dict]) -> dict:
    return {
        "tasks": len(results),
        "syntax_valid": sum(row["syntax_valid"] for row in results),
        "expected_function_found": sum(row["expected_function_found"] for row in results),
        "mean_latency_ms": round(statistics.mean(row["latency_ms"] for row in results)) if results else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report path (default: artifacts/model-evaluation.json).")
    args = parser.parse_args()

    tasks = json.loads(TASK_FILE.read_text(encoding="utf-8"))
    app = create_app()  # Loads .env and initializes the same local templates as the web app.
    status = model_status()
    if not status["configured"]:
        raise SystemExit(status["hint"] or "Configure a model before running this evaluation.")

    with app.app_context():
        connection = get_db()
        examples = [
            {
                "keywords": json.loads(row["keywords_json"]),
                "code": row["code"],
            }
            for row in connection.execute(
                "SELECT keywords_json, code FROM examples WHERE enabled = 1 ORDER BY title"
            ).fetchall()
        ]

    local_rows = []
    model_rows = []
    for task in tasks:
        started = time.perf_counter()
        local_output = generate_code(task["prompt"], examples)
        local_latency = round((time.perf_counter() - started) * 1000)
        local_rows.append({"task_id": task["id"], **assess(local_output, task["expected_function"]), "latency_ms": local_latency})

        model_result = ask_model("generate", task["prompt"], "beginner")
        model_rows.append({"task_id": task["id"], **assess(model_result["text"], task["expected_function"]), "latency_ms": model_result["duration_ms"]})
        print(f"Completed {task['id']}")

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": status["provider"],
        "model": status["model"],
        "rubric": "Parseable Python and presence of the requested function name. Generated code is not executed; this is not a functional-correctness score.",
        "local_generator": {"summary": summarize(local_rows), "tasks": local_rows},
        "configured_model": {"summary": summarize(model_rows), "tasks": model_rows},
    }
    output_path = args.output or ROOT / "artifacts" / "model-evaluation.json"
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"local_generator": report["local_generator"]["summary"], "configured_model": report["configured_model"]["summary"], "report": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModelError as error:
        raise SystemExit(str(error)) from error

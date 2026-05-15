# Agent loop: 3 custom tools (read_data, run_python, submit_answer) over the Anthropic SDK.
# Trajectory JSON logger writes a self-contained record per run (design doc §7).
# Multi-task runner lives in a follow-up plan.

import io
import json
import time
import traceback
import uuid
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import numpy as np
import pandas as pd
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

client = anthropic.Anthropic()

BENCHMARK_DIR = Path("benchmark_data")
TRAJECTORIES_DIR = Path("trajectories")
MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 12
MAX_TOKENS = 4096
TOOL_OUTPUT_TRUNCATE_CHARS = 5000


TOOLS = [
    {
        "type": "custom",
        "name": "read_data",
        "description": (
            "Read a CSV or text file from the benchmark_data directory. "
            "Returns the full file content as a string plus basic metadata (row count, size)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_name": {
                    "type": "string",
                    "description": "Filename inside benchmark_data/, e.g. 'task_01_revenue_concentration.csv'.",
                }
            },
            "required": ["file_name"],
        },
    },
    {
        "type": "custom",
        "name": "run_python",
        "description": (
            "Execute Python code in a persistent namespace with pandas (pd) and numpy (np) preloaded. "
            "Variables and dataframes persist across calls within a single task. "
            "Returns captured stdout, stderr, and an error traceback if the code raised."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source to execute. Use print() to surface values into stdout.",
                }
            },
            "required": ["code"],
        },
    },
    {
        "type": "custom",
        "name": "submit_answer",
        "description": (
            "Submit the final structured answer for grading. Calling this terminates the agent loop. "
            "Call it exactly once, only when you are ready to commit to a final answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "description": "The structured result for the task. Shape varies per task — see task prompt.",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Short summary of how the answer was derived.",
                },
                "flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of QoE risks or concerns the agent identified.",
                },
            },
            "required": ["answer", "reasoning", "flags"],
        },
    },
]


# Persistent namespace for run_python. Reset between tasks by the sweep runner.
_PY_NAMESPACE: dict = {"pd": pd, "np": np}


def _reset_py_namespace():
    _PY_NAMESPACE.clear()
    _PY_NAMESPACE.update({"pd": pd, "np": np})


def read_data(file_name: str) -> dict:
    path = BENCHMARK_DIR / file_name
    if not path.exists():
        return {
            "error": f"file not found: {file_name}",
            "available_files": sorted(p.name for p in BENCHMARK_DIR.glob("*.csv")),
        }
    content = path.read_text()
    return {
        "file_name": file_name,
        "content": content,
        "row_count": content.count("\n"),
        "size_bytes": len(content.encode()),
    }


def run_python(code: str) -> dict:
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            exec(code, _PY_NAMESPACE)
        return {"stdout": out.getvalue(), "stderr": err.getvalue(), "error": None}
    except Exception:
        return {
            "stdout": out.getvalue(),
            "stderr": err.getvalue(),
            "error": traceback.format_exc(),
        }


def submit_answer(answer, reasoning: str, flags: list) -> dict:
    # Required-field validation is enforced by Anthropic against input_schema before this
    # call lands. Return value is a trivial confirmation; the loop captures the actual
    # answer payload from tool_use.input and terminates.
    return {"status": "accepted", "message": "Answer recorded. Task complete."}


_TOOL_DISPATCH = {
    "read_data": read_data,
    "run_python": run_python,
    "submit_answer": submit_answer,
}


def run_tool(name: str, tool_input: dict) -> dict:
    fn = _TOOL_DISPATCH.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return fn(**tool_input)
    except TypeError as e:
        return {"error": f"bad tool input for {name}: {e}"}


def _create_message(messages: list):
    return client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=TOOLS,
        tool_choice={"type": "auto", "disable_parallel_tool_use": True},
        messages=messages,
    )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _truncate(s: str, limit: int = TOOL_OUTPUT_TRUNCATE_CHARS) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + "<truncated>"


def _content_to_jsonable(content):
    # User messages we constructed are already plain dicts/strings; assistant
    # content from response.content is a list of pydantic blocks with model_dump().
    if isinstance(content, str):
        return content
    out = []
    for block in content:
        if hasattr(block, "model_dump"):
            out.append(block.model_dump())
        else:
            out.append(block)
    return out


def run_task(task_id: str = "task_01") -> dict:
    """Run one task end-to-end and return the trajectory dict (also written to disk)."""
    _reset_py_namespace()
    prompt_path = BENCHMARK_DIR / f"{task_id}_prompt_lean.md"
    answer_path = BENCHMARK_DIR / f"{task_id}_answer.json"
    task_prompt = prompt_path.read_text()
    reference_answer = json.loads(answer_path.read_text()) if answer_path.exists() else None

    trajectory = {
        "task_id": task_id,
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model": MODEL,
        "task_prompt": task_prompt,
        "reference_answer": reference_answer,
        "messages": [],
        "tool_calls": [],
        "final_answer": None,
        "iterations": 0,
        "terminated_by": None,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }

    def _log_message(role: str, content) -> int:
        turn = len(trajectory["messages"]) + 1
        trajectory["messages"].append({
            "turn": turn,
            "role": role,
            "content": _content_to_jsonable(content),
            "timestamp_ms": _now_ms(),
        })
        return turn

    messages = [{"role": "user", "content": task_prompt}]
    _log_message("user", task_prompt)

    try:
        response = _create_message(messages)
        trajectory["total_input_tokens"] += response.usage.input_tokens
        trajectory["total_output_tokens"] += response.usage.output_tokens

        for iteration in range(MAX_ITERATIONS):
            trajectory["iterations"] = iteration + 1
            assistant_turn = _log_message("assistant", response.content)

            if response.stop_reason != "tool_use":
                trajectory["terminated_by"] = response.stop_reason  # usually "end_turn"
                break

            tool_use = next(b for b in response.content if b.type == "tool_use")

            t0 = time.perf_counter()
            try:
                result = run_tool(tool_use.name, tool_use.input)
                tool_error = None
            except Exception:
                result = {"error": "tool dispatcher raised"}
                tool_error = traceback.format_exc()
            duration_ms = int((time.perf_counter() - t0) * 1000)

            result_json = json.dumps(result, default=str)
            trajectory["tool_calls"].append({
                "tool_use_id": tool_use.id,
                "turn": assistant_turn,
                "tool_name": tool_use.name,
                "input": dict(tool_use.input),
                "output": _truncate(result_json),
                "duration_ms": duration_ms,
                "error": tool_error,
            })
            print(f"Tool: {tool_use.name}  input keys: {list(tool_use.input.keys())}  ({duration_ms}ms)")

            messages.append({"role": "assistant", "content": response.content})
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result_json,
            }
            messages.append({"role": "user", "content": [tool_result_block]})
            _log_message("tool_result", [tool_result_block])

            if tool_use.name == "submit_answer":
                trajectory["final_answer"] = dict(tool_use.input)
                trajectory["terminated_by"] = "submit_answer"
                break

            response = _create_message(messages)
            trajectory["total_input_tokens"] += response.usage.input_tokens
            trajectory["total_output_tokens"] += response.usage.output_tokens
        else:
            trajectory["terminated_by"] = "max_iterations"

    except Exception:
        trajectory["terminated_by"] = "error"
        trajectory["error"] = traceback.format_exc()

    TRAJECTORIES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TRAJECTORIES_DIR / f"{task_id}_{trajectory['run_id']}.json"
    out_path.write_text(json.dumps(trajectory, indent=2, default=str))

    print(f"\n--- terminated_by: {trajectory['terminated_by']} ---")
    print(f"iterations: {trajectory['iterations']}  "
          f"tokens in/out: {trajectory['total_input_tokens']}/{trajectory['total_output_tokens']}")
    print(f"trajectory: {out_path}")
    return trajectory


def discover_tasks() -> list[str]:
    return sorted(p.name.removesuffix("_prompt_lean.md")
                  for p in BENCHMARK_DIR.glob("task_*_prompt_lean.md"))


def run_all_tasks() -> dict:
    """Run every task discovered in benchmark_data/ sequentially. Returns the batch summary."""
    task_ids = discover_tasks()
    batch = {
        "batch_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "model": MODEL,
        "task_count": len(task_ids),
        "runs": [],
    }

    for task_id in task_ids:
        print(f"\n=== {task_id} ===")
        t = run_task(task_id)
        batch["runs"].append({
            "task_id": t["task_id"],
            "run_id": t["run_id"],
            "terminated_by": t["terminated_by"],
            "iterations": t["iterations"],
            "input_tokens": t["total_input_tokens"],
            "output_tokens": t["total_output_tokens"],
            "trajectory_path": str(TRAJECTORIES_DIR / f"{t['task_id']}_{t['run_id']}.json"),
        })

    TRAJECTORIES_DIR.mkdir(parents=True, exist_ok=True)
    batch_path = TRAJECTORIES_DIR / f"batch_{batch['batch_id']}.json"
    batch_path.write_text(json.dumps(batch, indent=2))

    print("\n=== batch summary ===")
    print(f"batch_id: {batch['batch_id']}")
    print(f"{'task_id':<10} {'terminated_by':<16} {'iters':>6} {'in_tok':>8} {'out_tok':>8}")
    for r in batch["runs"]:
        print(f"{r['task_id']:<10} {r['terminated_by']:<16} {r['iterations']:>6} "
              f"{r['input_tokens']:>8} {r['output_tokens']:>8}")
    totals_in = sum(r["input_tokens"] for r in batch["runs"])
    totals_out = sum(r["output_tokens"] for r in batch["runs"])
    print(f"{'TOTAL':<10} {'':<16} {'':>6} {totals_in:>8} {totals_out:>8}")
    print(f"batch summary: {batch_path}")
    return batch


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_task(sys.argv[1])
    else:
        run_all_tasks()

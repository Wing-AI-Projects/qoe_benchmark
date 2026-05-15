# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A 6-task agent benchmark for Quality-of-Earnings (QoE) financial diligence. An agent loop (Anthropic SDK + 3 custom tools) reads CSVs, computes answers in a Python sandbox, and submits structured results. A separate grader scores trajectories on a 3-dimension rubric (correctness / tool use / reasoning).

[README.md](README.md) covers the high-level rationale (no-framework choice, tool design, rubric, known limitations). This file focuses on operational gotchas when modifying the code.

## Commands

Setup:
```bash
# Requires ANTHROPIC_API_KEY in .env (already present)
pip install anthropic pandas numpy python-dotenv
```

Run the agent:
```bash
python agent.py                # run all tasks discovered in benchmark_data/
python agent.py task_03        # run a single task by id
```

Grade trajectories:
```bash
python grader.py               # grade the most recent batch_*.json in trajectories/
python grader.py <batch_uuid>  # grade a specific batch
python grader.py trajectories/task_01_<run_id>.json   # grade one trajectory
```

There are no tests, no linter, no build step. The "tests" are the benchmark tasks themselves — running `agent.py` then `grader.py` end-to-end is the validation loop.

## Architecture

Two scripts, two data directories, one loop each.

**[agent.py](agent.py) — agent loop.** Single Anthropic `messages.create` loop with `disable_parallel_tool_use=True`, max 12 iterations. Three custom tools:
- `read_data(file_name)` — reads a file from `benchmark_data/` and returns full contents + metadata.
- `run_python(code)` — `exec` in a module-level namespace (`_PY_NAMESPACE`) preloaded with `pd`/`np`. **State persists across calls within a task and is reset between tasks via `_reset_py_namespace()`.** This is intentional — the agent should be able to build dataframes incrementally.
- `submit_answer(answer, reasoning, flags)` — terminates the loop. The return value is just a confirmation; the real answer payload is captured from `tool_use.input` in the loop, not from the function's return.

Every run writes a self-contained trajectory JSON to `trajectories/task_<id>_<run_uuid>.json`. `run_all_tasks()` additionally writes `batch_<uuid>.json` summarising the runs — the grader keys off these batch files.

**[grader.py](grader.py) — three-dimension rubric.** Each trajectory gets three scores 0-3:
- **Correctness** — deterministic: numeric fields checked against per-field `tolerance` specs in the answer JSON (`dollar`, `ratio_pct`, `exact_string`, `set_overlap`); flag matching done by an LLM judge (semantic). Score composition rules are hard-coded in `grade_correctness()`.
- **Tool use** — deterministic gate (must use all `minimum_tools_required`), then LLM judge against `tool_use_criteria.good_pattern` / `anti_patterns`.
- **Reasoning** — pure LLM judge over the abridged conversation.

The judge uses forced tool calls (`tool_choice={"type": "tool", ...}`) with single-purpose tools (`record_grade`, `record_flag_match`) — this is the structured-output pattern; do not switch it to free-text parsing.

Grades land in `grades/<batch_uuid>/`, with `report.md` aggregating per-task scores and rationales.

**Models** are hard-coded at module top: agent uses `claude-sonnet-4-6`, judge uses `claude-opus-4-7`. Change them there, not via env.

## Benchmark data layout

`benchmark_data/` holds, per task id `task_NN`:
- `task_NN_prompt.md` — long-form prompt with full task framing.
- `task_NN_prompt_lean.md` — **the file the agent actually receives**. `run_task` reads `_prompt_lean.md`, not `_prompt.md`.
- `task_NN_<dataset>.csv` — one or more input CSVs the agent reads via `read_data`.
- `task_NN_answer.json` — reference answer plus three grading sections: `tolerance` (per-field deterministic check), `expected_flags` (semantic judge), `tool_use_criteria` (judge grounding).

When adding a task: discovery is by `task_*_prompt_lean.md` glob, so the lean prompt is what gates inclusion in a sweep. The answer JSON's schema must match what `_check_field` expects — see existing files for the shape.

The grader always reads the current on-disk `task_NN_answer.json` for rubric criteria, never the `reference_answer` embedded in old trajectories. This is intentional: the rubric can evolve without re-running the agent.

## Things to know before changing code

- The persistent Python namespace is module-global. If you parallelise task execution, you must rework `_PY_NAMESPACE` or you will get cross-task contamination.
- Tool result content is JSON-stringified before being sent back to the model (see the `tool_result_block` construction); the trajectory log truncates outputs to `TOOL_OUTPUT_TRUNCATE_CHARS` (5000) but the *model* sees the full result. Keep that distinction.
- `.env` (gitignored) holds `ANTHROPIC_API_KEY`. Copy `.env.example` and fill it in to run locally.

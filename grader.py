# Grader: deterministic + LLM-as-judge across the three §8 rubric dimensions.
# Reads trajectories produced by agent.py; writes per-trajectory grade JSONs
# plus an aggregate markdown report per batch.

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
client = anthropic.Anthropic()

REPO = Path("/Users/wing/AIProjects/QoE_Benchmark")
BENCHMARK_DIR = REPO / "benchmark_data"
TRAJ_DIR = REPO / "trajectories"
GRADES_DIR = REPO / "grades"
JUDGE_MODEL = "claude-opus-4-7"
JUDGE_MAX_TOKENS = 1024


def _current_reference(task_id: str) -> dict:
    """Load the on-disk answer file. Always preferred over trajectory-embedded
    reference_answer for grading criteria, so the rubric can evolve without
    re-running trajectories."""
    return json.loads((BENCHMARK_DIR / f"{task_id}_answer.json").read_text())


# ---------- Deterministic helpers ----------

def _check_field(spec: dict, ref_val, agent_val) -> tuple[bool, str]:
    t = spec["type"]
    if agent_val is None:
        return False, "missing"
    if t == "dollar":
        diff = abs(float(agent_val) - float(ref_val))
        return diff <= spec["abs"], f"abs_diff=${diff:.2f} tol=${spec['abs']}"
    if t == "ratio_pct":
        diff = abs(float(agent_val) - float(ref_val))
        return diff <= spec["abs"], f"abs_diff={diff:.3f}pp tol={spec['abs']}pp"
    if t == "exact_string":
        ok = str(agent_val).strip().lower() == str(ref_val).strip().lower()
        return ok, f"agent={agent_val!r} ref={ref_val!r}"
    if t == "set_overlap":
        haystack = " | ".join(json.dumps(item).lower() for item in (agent_val or []))
        matches = sum(1 for s in spec["required_descriptions"] if s.lower() in haystack)
        return matches >= spec["min_match"], f"matched {matches}/{spec['min_match']} required substrings"
    return False, f"unknown tolerance type: {t}"


def _required_tools_used(trajectory: dict, criteria: dict) -> tuple[bool, list[str]]:
    used = {tc["tool_name"] for tc in trajectory["tool_calls"]}
    required = set(criteria["minimum_tools_required"])
    missing = sorted(required - used)
    return (not missing), missing


# ---------- Judge plumbing ----------

_RECORD_GRADE_TOOL = {
    "type": "custom",
    "name": "record_grade",
    "description": "Record a 0-3 grade with a brief rationale.",
    "input_schema": {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "enum": [0, 1, 2, 3]},
            "rationale": {"type": "string"},
        },
        "required": ["score", "rationale"],
    },
}

_RECORD_FLAGS_TOOL = {
    "type": "custom",
    "name": "record_flag_match",
    "description": "Record which expected flags are semantically present in the agent's flag list.",
    "input_schema": {
        "type": "object",
        "properties": {
            "missing_flags": {"type": "array", "items": {"type": "string"}},
            "extra_flags": {"type": "array", "items": {"type": "string"}},
            "all_present": {"type": "boolean"},
            "any_present": {"type": "boolean"},
            "summary": {"type": "string"},
        },
        "required": ["missing_flags", "extra_flags", "all_present", "any_present", "summary"],
    },
}


def _force_tool_call(system: str, user: str, tool: dict) -> dict:
    """Single-turn judge call. Forces the model to emit the given tool's input."""
    resp = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=JUDGE_MAX_TOKENS,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": user}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return dict(block.input)
    raise RuntimeError(f"judge did not emit {tool['name']}; stop_reason={resp.stop_reason}")


# ---------- Dimension 1: correctness ----------

_FLAG_JUDGE_SYSTEM = """You compare an agent's flagged QoE concerns against a list of expected flags.
Flags are short strings about specific risks; phrasing varies. Match by semantic intent, not wording.
A flag is "present" if any of the agent's flags conveys the same underlying concern as the expected flag.
Output via the record_flag_match tool."""


def _judge_flags(expected: list[str], actual: list[str]) -> dict:
    user = (
        f"EXPECTED FLAGS:\n{json.dumps(expected, indent=2)}\n\n"
        f"AGENT'S FLAGS:\n{json.dumps(actual, indent=2)}\n\n"
        "For each expected flag, decide if any agent flag conveys the same concern. "
        "List expected flags not present as missing_flags. List agent flags that don't "
        "correspond to any expected flag as extra_flags. Set all_present=true if no "
        "missing_flags, any_present=true if at least one expected flag is present."
    )
    return _force_tool_call(_FLAG_JUDGE_SYSTEM, user, _RECORD_FLAGS_TOOL)


def grade_correctness(trajectory: dict) -> dict:
    ref = _current_reference(trajectory["task_id"])
    final = trajectory["final_answer"]

    if final is None or trajectory["terminated_by"] != "submit_answer":
        return {
            "score": 0,
            "rationale": f"no submit_answer (terminated_by={trajectory['terminated_by']})",
            "deterministic": {"submitted": False},
        }

    field_results = {}
    for field, spec in ref["tolerance"].items():
        ok, detail = _check_field(spec, ref["answer"].get(field), final.get("answer", {}).get(field))
        field_results[field] = {"ok": ok, "detail": detail}
    numeric_passed = sum(1 for r in field_results.values() if r["ok"])
    numeric_total = len(field_results)
    numeric_perfect = numeric_passed == numeric_total

    flag_match = _judge_flags(ref["expected_flags"], final.get("flags", []))

    if numeric_perfect and flag_match["all_present"]:
        score = 3
    elif numeric_passed >= numeric_total - 1 and flag_match["any_present"]:
        score = 2
    elif numeric_passed >= max(1, numeric_total // 2):
        score = 1
    else:
        score = 0

    return {
        "score": score,
        "rationale": (
            f"numeric {numeric_passed}/{numeric_total} within tolerance; "
            f"flags: {flag_match['summary']}"
        ),
        "deterministic": {"fields": field_results, "flags": flag_match},
    }


# ---------- Dimension 2: tool use ----------

_TOOL_USE_JUDGE_SYSTEM = """You are grading an AI agent's tool use on a QoE diligence task.
Score 0-3 using these anchors verbatim:

3: Used all minimum_tools_required. Sequence matches or improves on good_pattern.
   No redundant calls. Tool inputs are well-formed.
2: Used all required tools and produced a workable sequence, but with 1-2 inefficiencies:
   minor redundant call, suboptimal ordering, or one unnecessary tool invocation.
1: Clear inefficiency or partial mismatch with good_pattern. Missing a recommended tool,
   OR multiple redundant calls, OR triggered an anti_pattern.
0: (reserved for missing a minimum_tools_required tool, already deterministically caught).

Be strict. Cite which good_pattern step or anti_pattern applied. Output via the record_grade tool."""


def _judge_tool_use(tool_calls: list[dict], criteria: dict) -> dict:
    compact_calls = [
        {
            "n": i + 1,
            "tool": tc["tool_name"],
            "input_keys": sorted(tc["input"].keys()),
            "input_preview": {k: (str(v)[:200] + "...") if isinstance(v, str) and len(str(v)) > 200 else v
                              for k, v in tc["input"].items()},
            "duration_ms": tc["duration_ms"],
            "error": tc["error"],
        }
        for i, tc in enumerate(tool_calls)
    ]
    user = (
        f"GROUNDING:\n{json.dumps(criteria, indent=2)}\n\n"
        f"AGENT'S TOOL CALL SEQUENCE ({len(tool_calls)} calls):\n"
        f"{json.dumps(compact_calls, indent=2)}\n\n"
        "Score the tool-use quality against the grounding. Cite specific call numbers."
    )
    out = _force_tool_call(_TOOL_USE_JUDGE_SYSTEM, user, _RECORD_GRADE_TOOL)
    return {"score": out["score"], "rationale": out["rationale"], "deterministic": None}


def grade_tool_use(trajectory: dict) -> dict:
    criteria = _current_reference(trajectory["task_id"])["tool_use_criteria"]
    ok, missing = _required_tools_used(trajectory, criteria)
    if not ok:
        return {
            "score": 0,
            "rationale": f"missing required tools: {missing}",
            "deterministic": {"missing": missing},
        }
    return _judge_tool_use(trajectory["tool_calls"], criteria)


# ---------- Dimension 3: reasoning ----------

_REASONING_JUDGE_SYSTEM = """You are grading an AI agent's reasoning quality on a QoE diligence task.
Score 0-3 using these anchors verbatim:

3: Each reasoning step follows from the previous. The agent is explicit about
   assumptions (e.g., 'using a 90-day cutoff per the task prompt'). Edge cases
   or ambiguity surfaced rather than glossed over. Reasoning traces to the data.
2: Coherent overall and supports the final answer, but with some unstated
   assumptions or skipped intermediate steps. A careful reader can follow it
   but must fill 1-2 gaps. May miss flagging an edge case a strong analyst would name.
1: Visible gaps or unjustified jumps. Conclusion may be right but path unclear,
   OR the agent reasons confidently about something it should have flagged uncertain.
0: No coherent reasoning. Post-hoc justification of a guessed answer,
   contradicts the data, or missing entirely.

Be a strict grader. Cite specific turn numbers or content when justifying.
Output via the record_grade tool."""


def _compact_messages_for_judge(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = m["role"]
        content = m["content"]
        if isinstance(content, str):
            lines.append(f"[turn {m['turn']}] {role}: {content[:1500]}")
            continue
        for block in content:
            btype = block.get("type")
            if btype == "text":
                lines.append(f"[turn {m['turn']}] {role} text: {block.get('text','')[:1500]}")
            elif btype == "tool_use":
                # show only the call header; full input is in tool_calls already
                inp_keys = sorted((block.get("input") or {}).keys())
                lines.append(f"[turn {m['turn']}] {role} tool_use: {block.get('name')} input_keys={inp_keys}")
            elif btype == "tool_result":
                txt = block.get("content", "")
                if isinstance(txt, list):
                    txt = json.dumps(txt)
                lines.append(f"[turn {m['turn']}] tool_result: {str(txt)[:800]}")
    return "\n".join(lines)


def grade_reasoning(trajectory: dict) -> dict:
    user = (
        f"TASK PROMPT:\n{trajectory['task_prompt']}\n\n"
        f"AGENT'S FINAL ANSWER:\n{json.dumps(trajectory['final_answer'], indent=2)}\n\n"
        f"CONVERSATION (abridged):\n{_compact_messages_for_judge(trajectory['messages'])}\n\n"
        "Score this trajectory's reasoning quality against the rubric."
    )
    out = _force_tool_call(_REASONING_JUDGE_SYSTEM, user, _RECORD_GRADE_TOOL)
    return {"score": out["score"], "rationale": out["rationale"], "deterministic": None}


# ---------- Orchestration ----------

def grade_trajectory(trajectory_path: Path | str) -> dict:
    path = Path(trajectory_path)
    traj = json.loads(path.read_text())
    return {
        "task_id": traj["task_id"],
        "run_id": traj["run_id"],
        "judge_model": JUDGE_MODEL,
        "graded_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "correctness": grade_correctness(traj),
        "tool_use": grade_tool_use(traj),
        "reasoning": grade_reasoning(traj),
        "trajectory_path": str(path),
        "terminated_by": traj["terminated_by"],
    }


def _resolve_batch_path(batch_id: str | None) -> Path:
    batches = sorted(TRAJ_DIR.glob("batch_*.json"), key=lambda p: p.stat().st_mtime)
    if not batches:
        raise FileNotFoundError(f"no batch files in {TRAJ_DIR}")
    if batch_id is None:
        return batches[-1]
    # accept "batch_<uuid>" or just "<uuid>"
    target = batch_id if batch_id.startswith("batch_") else f"batch_{batch_id}"
    for p in batches:
        if p.stem == target:
            return p
    raise FileNotFoundError(f"no batch matching {batch_id}")


def _render_report_md(batch: dict, grades: list[dict]) -> str:
    lines = []
    lines.append(f"# Grade report — `{batch['batch_id']}`\n")
    lines.append(f"- Agent model: `{batch['model']}`")
    lines.append(f"- Judge model: `{JUDGE_MODEL}`")
    lines.append(f"- Tasks graded: {len(grades)}")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')}\n")

    lines.append("## Per-task scores\n")
    lines.append("| task | terminated_by | correctness | tool_use | reasoning | sum/9 |")
    lines.append("|---|---|---|---|---|---|")
    sums = {"correctness": 0, "tool_use": 0, "reasoning": 0}
    for g in grades:
        c, t, r = g["correctness"]["score"], g["tool_use"]["score"], g["reasoning"]["score"]
        sums["correctness"] += c
        sums["tool_use"] += t
        sums["reasoning"] += r
        lines.append(f"| {g['task_id']} | {g['terminated_by']} | {c} | {t} | {r} | {c+t+r} |")

    n = len(grades) or 1
    lines.append("\n## Per-dimension averages\n")
    lines.append(f"- Correctness: **{sums['correctness']/n:.2f} / 3**")
    lines.append(f"- Tool use:    **{sums['tool_use']/n:.2f} / 3**")
    lines.append(f"- Reasoning:   **{sums['reasoning']/n:.2f} / 3**")
    overall = (sums['correctness'] + sums['tool_use'] + sums['reasoning']) / (3 * n)
    lines.append(f"- **Overall mean ({3*n} cells, equally weighted): {overall:.2f} / 3**\n")

    lines.append("## Per-task rationale\n")
    for g in grades:
        lines.append(f"<details><summary><strong>{g['task_id']}</strong> "
                     f"(c={g['correctness']['score']}, t={g['tool_use']['score']}, r={g['reasoning']['score']})</summary>\n")
        lines.append(f"- **Correctness:** {g['correctness']['rationale']}")
        lines.append(f"- **Tool use:** {g['tool_use']['rationale']}")
        lines.append(f"- **Reasoning:** {g['reasoning']['rationale']}")
        lines.append("\n</details>\n")

    return "\n".join(lines)


def grade_batch(batch_id: str | None = None) -> Path:
    batch_path = _resolve_batch_path(batch_id)
    batch = json.loads(batch_path.read_text())
    out_dir = GRADES_DIR / batch["batch_id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    grades = []
    for run in batch["runs"]:
        print(f"  grading {run['task_id']}...")
        g = grade_trajectory(run["trajectory_path"])
        (out_dir / f"{g['task_id']}_{g['run_id']}_grade.json").write_text(
            json.dumps(g, indent=2)
        )
        grades.append(g)
        print(f"    c={g['correctness']['score']} t={g['tool_use']['score']} r={g['reasoning']['score']}")

    report = out_dir / "report.md"
    report.write_text(_render_report_md(batch, grades))
    print(f"\ngrades written: {out_dir}")
    print(f"report: {report}")
    return out_dir


if __name__ == "__main__":
    if len(sys.argv) == 1:
        grade_batch(None)
    else:
        arg = sys.argv[1]
        if arg.endswith(".json") and Path(arg).is_file():
            g = grade_trajectory(arg)
            print(json.dumps(g, indent=2))
        else:
            grade_batch(arg)

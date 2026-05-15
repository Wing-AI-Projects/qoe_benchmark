# QoE Diligence Capability Evaluation — Scope of Engagement

*Prepared by Turing for a frontier-lab post-training team · v1 proposal*

This engagement produces a versioned, expert-calibrated benchmark for Quality-of-Earnings (QoE) financial diligence. Its purpose is narrow and decision-shaped: give the post-training team a defensible answer to *can this model be shipped as a QoE-grade analyst assistant, and if not, exactly where does it break.*

---

## 1. Capability target

The capability under test is **structured-data financial reasoning on QoE artifacts** — the agent is given heterogeneous source files (general ledger detail, customer rosters, AR aging schedules), asked a diligence question, and must read the data, pick the right computation, execute it, and defend the answer with an inspectable trail.

QoE is the right target because it is high-stakes, auditable, and forces a tight loop between *getting the number right* and *justifying the method*. A model that performs here is a credible candidate for the broader class of regulated knowledge-worker workflows where wrong answers and unsupported answers fail in equally expensive ways.

"Good" at the trajectory level: correct numeric answer within tolerance, a minimum-viable tool path (no flailing), and reasoning a partner-track analyst would sign off on without revision.

---

## 2. Deliverable shapes

Four artifacts ship at end of engagement:

- **Trajectory corpus** — graded JSON runs, one per task per model condition, fully self-contained (prompt, tool calls, tool results, final answer, token accounting).
- **Rubric specification** — versioned tolerance + LLM-judge anchors, stored *alongside* the tasks rather than inside the grader. Rubric can be tightened later without re-running the agent.
- **Aggregate scorecard** — per-capability pass rates, failure-mode taxonomy, calibration statistics against the expert panel.
- **Re-grade tooling** — one-command re-score of the existing trajectory corpus against any rubric version.

**Explicit non-deliverables**: no fine-tuning recommendations, no production deployment guidance, no use of real client data. These are listed so any expansion is a written conversation, not a surprise.

---

## 3. Scope

| Dimension | v1 commitment |
|---|---|
| **Tasks** | ~200, balanced across 8 sub-capability buckets |
| **Buckets** | Revenue concentration · AR/AP aging · Run-rate normalization · Customer churn impact · Non-recurring expense ID · EBITDA reconstruction · Working-capital adjustments · Cash-flow conversion |
| **Difficulty tiers** | 3 per bucket: clean / messy (mixed formats, footnotes) / adversarial (excerpts adapted from public 10-Ks) |
| **Rubric dimensions** | 3, 0–3 scale: correctness · tool use · reasoning |
| **Model conditions** | Target model + one baseline frontier model, so scores are comparative |
| **Calibration set** | 50 trajectories scored by a 3-rater expert panel |

The v0.1 pilot (this repo) covers the first six buckets at 1 task each. Pilot evidence supports the bucket structure as a workable taxonomy; the v1 expansion is *more* coverage and *harder* coverage, not a re-architecture.

---

## 4. Acceptance criteria

The engagement does not close until all four are met:

- **Coverage** — ≥ 20 tasks per sub-capability bucket; ≥ 5 per difficulty tier.
- **Calibration** — Cohen's κ ≥ 0.7 between the LLM-as-judge and the expert panel on the 50-trajectory calibration set. This is the load-bearing acceptance criterion — without it, every downstream score is decorative.
- **Reproducibility** — every trajectory regenerable from the corpus with a single command; rubric version stamped on every grade record.
- **Reusability** — rubric can be tightened post-handoff and the corpus re-graded without re-running the agent.

---

## 5. Timeline

| Week | Workstream | Output |
|---|---|---|
| 1–2 | Discovery + task taxonomy workshops with lab researchers and 2 domain experts | Final 8-bucket taxonomy; rater panel booked |
| 3–4 | Pilot: 10 tasks/bucket authored end-to-end, expert review | Rubric v0, task-authoring playbook |
| 5–7 | Full task corpus + synthetic data generation; adversarial tier authored against public 10-K excerpts | 200-task corpus frozen |
| 8 | Expert calibration panel: 50 trajectories, 3 raters | Human ground-truth scores |
| 9 | Full sweep across both model conditions; judge tuning until κ ≥ 0.7 | Calibrated judge prompts |
| 10 | Report, handoff, re-grade tooling walkthrough | Scorecard, taxonomy, all artifacts |

Total: **10 weeks** to a calibrated, reproducible benchmark.

---

## 6. Risks

- **Domain-expert availability** — the 3-rater panel is the most schedule-sensitive resource. *Mitigation:* panel pre-booked in week 1 against a 4th named alternate; calibration set sized so a single rater can complete in two working days.
- **Synthetic data realism** — author-generated tasks risk testing the eval team's intuition rather than the model's capability. *Mitigation:* the adversarial tier is sourced from anonymized public 10-K language so the hardest 1/3 of the corpus is not authored by the eval team.
- **Judge calibration drift** — judge model version changes can silently move scores. *Mitigation:* judge model pinned by version string at task close; quarterly re-calibration sampling clause included in the handoff.
- **Scope creep into adjacent capabilities** (FP&A variance, tax memos, audit workpapers). *Mitigation:* §2's non-deliverables list is contractual; expansion is a separate engagement, not a v1 amendment.

---

## Appendix: v0.1 pilot evidence

This proposal is grounded in a 6-task pilot already running in this repository — same agent loop, same rubric shape, same trajectory format proposed for v1. A worked end-to-end run is at [`grades/04196acd-4f69-4a6a-8daf-62c09fb22f8c/report.md`](grades/04196acd-4f69-4a6a-8daf-62c09fb22f8c/report.md). Two scope decisions above are direct consequences of pilot findings: (1) the 3-tool serial loop was sufficient at the capability boundary tested — adding tools before scaling tasks would optimize the wrong axis; (2) the v0.1 known-limitations list ([README §Known limitations](README.md#known-limitations-v1)) is the explicit source of the calibration panel and adversarial tier in v1.

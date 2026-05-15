# Task: EBITDA bridge

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

`task_06_gl_detail.csv` — FY2024 general ledger detail spanning revenue, COGS, and operating expense accounts. Columns: `gl_account`, `account_type` (one of `revenue`, `cogs`, `opex`), `description`, `period`, `amount`.

## External figure (provided by management)

**Reported EBITDA per management financials: $1,950,000.**

This is your starting point. Your job is to bridge from reported EBITDA to adjusted EBITDA by identifying and quantifying standard QoE add-backs visible in the GL detail.

## Task

Build the EBITDA bridge:

1. Start from the reported EBITDA figure provided above.
2. Review the GL detail and identify standard QoE adjustments. Look for:
   - Non-recurring items (M&A advisory fees, severance, one-time IT or transformation projects, restructuring) — apply the same classification logic as a non-recurring expense analysis.
   - Owner compensation normalization — if a GL line item discloses that owner pay is above market rate, the excess (NOT the full line amount) is the add-back.
   - Any other clearly non-operating or non-recurring item that a buyer would normalize.
3. Sum the adjustments and compute adjusted EBITDA = reported + adjustments.
4. Verify that the reconciliation ties: reported + sum(adjustments) = adjusted.
5. Compute adjustment magnitude as a percent of reported EBITDA.

When you read a GL line item, parse the description carefully — the line amount and the add-back amount are not always the same number (e.g., a line representing owner compensation may state how much of the line is "above market" and therefore eligible for normalization).

## Output schema

```json
{
  "answer": {
    "reported_ebitda": <integer dollars>,
    "adjustments": [
      {
        "name": "<short name for the adjustment>",
        "amount": <integer dollars, the add-back amount (not the full GL line)>,
        "type": "add-back",
        "rationale": "<1 sentence on why this is a standard QoE adjustment>"
      }
    ],
    "total_adjustments": <integer dollars>,
    "adjusted_ebitda": <integer dollars>,
    "adjustment_pct_of_reported": <number, 1 decimal>
  },
  "reasoning": "<2-4 sentence summary of bridge construction>",
  "flags": ["<each flag as a short string>"]
}
```

Verify that `reported_ebitda + total_adjustments == adjusted_ebitda` before calling submit_answer.

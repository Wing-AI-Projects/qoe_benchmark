# Task: EBITDA bridge

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

`task_06_gl_detail.csv` — FY2024 GL detail spanning revenue, COGS, and operating expense accounts. Columns: `gl_account`, `account_type` (one of `revenue`, `cogs`, `opex`), `description`, `period`, `amount`.

## External figure (provided by management)

Reported EBITDA per management financials: $1,950,000.

## Task

Build the EBITDA bridge. Identify standard QoE adjustments visible in the GL detail, name each with its dollar amount and a one-sentence rationale, sum them, and report adjusted EBITDA. The reconciliation must tie: `reported_ebitda + total_adjustments == adjusted_ebitda`. Raise any flags you would surface to the buyer.

## Output schema

```json
{
  "answer": {
    "reported_ebitda": <integer dollars>,
    "adjustments": [
      {
        "name": "<short name>",
        "amount": <integer dollars>,
        "type": "add-back",
        "rationale": "<1 sentence>"
      }
    ],
    "total_adjustments": <integer dollars>,
    "adjusted_ebitda": <integer dollars>,
    "adjustment_pct_of_reported": <number, 1 decimal>
  },
  "reasoning": "<2-4 sentence summary>",
  "flags": ["<each flag as a short string>"]
}
```

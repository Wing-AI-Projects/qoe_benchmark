# Task: T3M annualized run rate vs LTM

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

`task_03_monthly_revenue.csv` — one row per month. Columns: `month` (YYYY-MM string), `revenue`.

## Reference date

2024-12-31

## Task

Compute T3M annualized revenue and LTM revenue ending at the reference date, the variance between them as a percent, the months used for T3M, and interpret whether the divergence reflects organic growth, a one-time spike, or seasonality. Raise any flags you would surface to the buyer.

## Output schema

```json
{
  "answer": {
    "t3m_revenue": <integer dollars>,
    "t3m_annualized": <integer dollars>,
    "ltm_revenue": <integer dollars>,
    "variance_pct": <number, 1 decimal>,
    "t3m_months": ["YYYY-MM", "YYYY-MM", "YYYY-MM"]
  },
  "reasoning": "<2-4 sentence summary including interpretation>",
  "flags": ["<each flag as a short string>"]
}
```

# Task: T3M annualized run rate vs LTM

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox with pandas, numpy, and the standard library.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

`task_03_monthly_revenue.csv` — one row per month for the trailing 18 months. Columns: `month` (YYYY-MM string), `revenue`.

## Reference date

**2024-12-31** — use this as the period anchor.

## Definitions

- **T3M revenue**: sum of revenue across the three most recent months ending at the reference date (i.e., October, November, and December 2024).
- **T3M annualized**: T3M revenue × 4. This represents the implied annualized run rate based on the most recent quarter.
- **LTM revenue**: sum of revenue across the trailing twelve months ending at the reference date (i.e., January through December 2024).
- **Variance %**: (T3M annualized − LTM) / LTM, expressed as a percent.

## Task

1. Compute T3M revenue, T3M annualized, and LTM revenue.
2. Compute the variance of T3M annualized vs LTM as a percent.
3. List the three months used for T3M.
4. Interpret the divergence: does the monthly time series suggest organic growth, a one-time spike, or seasonality? Surface this judgment in the `reasoning` field and any appropriate flag.

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

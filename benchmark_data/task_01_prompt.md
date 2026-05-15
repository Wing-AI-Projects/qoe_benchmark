# Task: Revenue concentration analysis

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence on a target company. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox with pandas, numpy, and the standard library. Use it for any non-trivial computation.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

`task_01_revenue_concentration.csv` — one row per customer for fiscal year 2024. Columns: `customer_id`, `customer_name`, `fiscal_year`, `revenue`.

## Task

Assess customer revenue concentration. Compute:

1. Total FY2024 revenue across all customers.
2. Top-1 customer's revenue as a percent of total revenue.
3. Top-3 customers' combined revenue as a percent of total revenue.
4. Top-5 customers' combined revenue as a percent of total revenue.
5. The customer name with the highest revenue.

## Output schema

Call `submit_answer` with this structure:

```json
{
  "answer": {
    "total_revenue": <integer dollars>,
    "top_1_pct": <number, 1 decimal place>,
    "top_3_pct": <number, 1 decimal place>,
    "top_5_pct": <number, 1 decimal place>,
    "top_customer": "<customer_name string>"
  },
  "reasoning": "<1-3 sentence summary of how you computed the answer>",
  "flags": ["<each flag as a short string; empty list if no flags apply>"]
}
```

Use `run_python` for the sorting and ratio computation — do not estimate percentages in natural language.

# Task: Revenue concentration analysis

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence on a target company. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

`task_01_revenue_concentration.csv` — one row per customer for fiscal year 2024. Columns: `customer_id`, `customer_name`, `fiscal_year`, `revenue`.

## Task

Run a customer revenue concentration analysis. Report total revenue, top-1, top-3, and top-5 concentration ratios, the top customer's name, and any flags you would raise to the buyer.

## Output schema

```json
{
  "answer": {
    "total_revenue": <integer dollars>,
    "top_1_pct": <number, 1 decimal place>,
    "top_3_pct": <number, 1 decimal place>,
    "top_5_pct": <number, 1 decimal place>,
    "top_customer": "<customer_name string>"
  },
  "reasoning": "<1-3 sentence summary>",
  "flags": ["<each flag as a short string; empty list if no flags>"]
}
```

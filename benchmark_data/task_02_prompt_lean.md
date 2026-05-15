# Task: Accounts receivable aging risk

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

`task_02_ar_aging.csv` — one row per open invoice. Columns: `invoice_id`, `customer_id`, `customer_name`, `invoice_date`, `due_date`, `amount`, `status`.

## Reference date

2025-01-31

## Task

Run an AR aging analysis using standard buckets: `current`, `1_30`, `31_60`, `61_90`, `90_plus` (days past due based on `due_date`). Report total AR, each bucket as a percent of total AR, identify the customer concentrating the largest share of the 90+ bucket, and raise any flags you would surface to the buyer.

## Output schema

```json
{
  "answer": {
    "total_ar": <integer dollars>,
    "current_pct": <number, 1 decimal>,
    "1_30_pct": <number, 1 decimal>,
    "31_60_pct": <number, 1 decimal>,
    "61_90_pct": <number, 1 decimal>,
    "90_plus_pct": <number, 1 decimal>,
    "top_aged_customer": "<customer_name string>",
    "top_aged_customer_pct_of_90plus": <number, 1 decimal>
  },
  "reasoning": "<1-3 sentence summary>",
  "flags": ["<each flag as a short string>"]
}
```

# Task: Accounts receivable aging risk

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox with pandas, numpy, and the standard library. Use it for date arithmetic and aggregation.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

`task_02_ar_aging.csv` — one row per open invoice. Columns: `invoice_id`, `customer_id`, `customer_name`, `invoice_date`, `due_date`, `amount`, `status`.

## Reference date

**2025-01-31** — use this as the "as of" date for aging.

## Aging convention

Compute days past due as `reference_date - due_date` (NOT invoice_date) and bucket each invoice as follows:

| Bucket name | Condition |
|---|---|
| `current` | days_past_due <= 0 (not yet due) |
| `1_30` | 1 to 30 days past due |
| `31_60` | 31 to 60 days past due |
| `61_90` | 61 to 90 days past due |
| `90_plus` | more than 90 days past due |

## Task

1. Compute total AR (sum of all open invoice amounts).
2. For each aging bucket, compute the percent of total AR.
3. Within the 90+ bucket, identify the customer holding the largest share of aged AR and what percent of the 90+ bucket they represent.

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
  "reasoning": "<1-3 sentence summary of approach>",
  "flags": ["<each flag as a short string; empty list if no flags apply>"]
}
```

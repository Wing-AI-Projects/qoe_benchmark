# Task: Customer churn impact (period-over-period)

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

Two files, both with columns `customer_id`, `customer_name`, `revenue`. Use `customer_id` as the join key.

- `task_04_customers_fy2023.csv` — prior period (FY2023).
- `task_04_customers_fy2024.csv` — current period (FY2024).

## Task

Analyze customer churn and retention between the two periods. Report total revenue for each period, churn count and dollar impact, the named list of churned customers, new customer count and dollar value, gross and net revenue retention, and the top churned customer's share of prior revenue. Raise any flags you would surface to the buyer.

## Output schema

```json
{
  "answer": {
    "prior_period_revenue": <integer dollars>,
    "current_period_revenue": <integer dollars>,
    "churned_customer_count": <integer>,
    "churned_customer_dollar_impact": <integer dollars>,
    "churned_customers": [
      {"customer_id": "<id>", "customer_name": "<name>", "prior_revenue": <int>}
    ],
    "new_customer_count": <integer>,
    "new_customers_dollar_value": <integer dollars>,
    "gross_revenue_retention_pct": <number, 1 decimal>,
    "net_revenue_retention_pct": <number, 1 decimal>,
    "top_churned_customer_pct_of_prior": <number, 1 decimal>
  },
  "reasoning": "<2-4 sentence summary>",
  "flags": ["<each flag as a short string>"]
}
```

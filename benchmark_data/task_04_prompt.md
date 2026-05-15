# Task: Customer churn impact (period-over-period)

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox with pandas, numpy, and the standard library.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

Two files, both with columns: `customer_id`, `customer_name`, `revenue`. You will need to read both.

- `task_04_customers_fy2023.csv` — prior period (FY2023) revenue by customer.
- `task_04_customers_fy2024.csv` — current period (FY2024) revenue by customer.

## Definitions

- **Churned customer**: present in FY2023 but absent in FY2024.
- **New customer**: present in FY2024 but absent in FY2023.
- **Retained customer**: present in both periods.
- **Gross revenue retention (GRR)**: sum across retained customers of `min(prior_revenue, current_revenue)` divided by total prior period revenue, expressed as a percent. GRR caps each customer's contribution at their prior level so upsell does not count.
- **Net revenue retention (NRR)**: sum across retained customers of `current_revenue` divided by total prior period revenue, expressed as a percent. NRR includes expansion on retained customers but EXCLUDES new logos.

Use `customer_id` as the join key.

## Task

Compute and report:

1. Total prior period revenue and total current period revenue.
2. Count and dollar impact of churned customers (sum of their prior-period revenue).
3. Named list of the churned customers (id, name, prior_revenue).
4. Count of new customers and the sum of their current-period revenue.
5. GRR and NRR per the definitions above.
6. The top churned customer's prior revenue as a percent of total prior period revenue.

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
  "reasoning": "<2-4 sentence summary including the headline-vs-underlying signal>",
  "flags": ["<each flag as a short string>"]
}
```

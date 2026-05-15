# Task: Non-recurring expense identification

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools available in the agent loop:

- `read_data(file_name)` — returns the raw contents of a CSV file.
- `run_python(code)` — executes Python in a sandbox. Useful for summing the filtered set of items once you've classified them.
- `submit_answer(answer, reasoning, flags)` — submits your final structured answer. Call this exactly once when you are done.

## Input

`task_05_gl_detail.csv` — FY2024 general ledger detail for operating expense accounts. Columns: `gl_account`, `description`, `period`, `amount`. Each row is a line item. Amounts can be negative for credits/recoveries.

## Task

Review every line item and classify each as either RECURRING or NON-RECURRING based on its description. Apply these criteria:

A line is **non-recurring** if any of the following are true:

1. The description explicitly states "one-time", "non-recurring", or names a discrete project (e.g., "Project Phoenix", "ERP migration").
2. The cost type is inherently non-recurring in normal QoE convention — severance, M&A advisory fees, transaction-related legal, restructuring.
3. The line shows a single occurrence within the fiscal year without an ongoing pattern.

A line is **recurring** if the cost type is operational (rent, salaries, payroll, utilities, ongoing legal, recurring software subscriptions, ongoing insurance, ongoing accounting, depreciation, etc.) and the description does not indicate one-time nature.

If a line item is **ambiguous** (you can construct a plausible case for either classification — e.g., a large settlement, an unusual insurance recovery, a one-time but possibly repeatable spend), do NOT include it in the non-recurring adjustment. Instead, surface it in `flags` for buyer review.

## Output

Compute total operating expenses (sum of all line items including any credits), the non-recurring total (sum of items you classified as non-recurring), and adjusted opex (total minus non-recurring).

When summarizing combined items in `non_recurring_items` (e.g., two ERP migration line items in different quarters), you may combine them under a single named entry as long as the amount is correctly summed.

## Output schema

```json
{
  "answer": {
    "total_opex": <integer dollars>,
    "non_recurring_items": [
      {
        "description": "<descriptor for the item or combined items>",
        "amount": <integer dollars>,
        "rationale": "<1 sentence on why this is non-recurring>"
      }
    ],
    "non_recurring_total": <integer dollars>,
    "adjusted_opex": <integer dollars>,
    "non_recurring_pct_of_opex": <number, 1 decimal>
  },
  "reasoning": "<2-4 sentence summary of your classification approach>",
  "flags": ["<each flag as a short string, including ambiguous items for review>"]
}
```

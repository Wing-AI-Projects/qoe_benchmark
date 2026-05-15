# Task: Non-recurring expense identification

You are a Quality of Earnings (QoE) analyst conducting buy-side due diligence. You have three tools: `read_data(file_name)`, `run_python(code)`, and `submit_answer(answer, reasoning, flags)`. Call submit_answer exactly once when you are done.

## Input

`task_05_gl_detail.csv` — FY2024 GL detail for operating expense accounts. Columns: `gl_account`, `description`, `period`, `amount`. Amounts can be negative for credits or recoveries.

## Task

Review the GL detail and identify items that should be added back as non-recurring for QoE purposes. Report total opex, the list of items you are adjusting (each with a one-sentence rationale), the non-recurring total, adjusted opex, and the non-recurring percent of opex. Surface any items where the classification is unclear so the buyer can review them — these do not belong in the adjustment total.

## Output schema

```json
{
  "answer": {
    "total_opex": <integer dollars>,
    "non_recurring_items": [
      {
        "description": "<descriptor for the item or combined items>",
        "amount": <integer dollars>,
        "rationale": "<1 sentence>"
      }
    ],
    "non_recurring_total": <integer dollars>,
    "adjusted_opex": <integer dollars>,
    "non_recurring_pct_of_opex": <number, 1 decimal>
  },
  "reasoning": "<2-4 sentence summary>",
  "flags": ["<each flag as a short string, including ambiguous items for review>"]
}
```

# Quick plan: topics, answers and example parses

Read this when you turn the user's own words into `save_plan_answers` calls. The tool's step text and the
`divid-planner://guide/interview` resource are the full, current list of fields; if they differ from this page, follow
them.

How saving works:

- One call per topic: `save_plan_answers` with the draft id, the topic (`stage`) and its answers.
- Keys you send replace what was saved; keys you leave out stay; a list is replaced whole.
- Money is US dollars. Percents are 0 to 100. The drop the user could sit through is a fraction (0.1 = 10%).
- A rough answer is fine. Save it, then confirm with the words and numbers the tool returns.
- Plan months are numbers from 1 (the month after the market data date). The step text shows the calendar span, for
  example "1-12 = Oct 2026 to Sep 2027". Say the calendar month to the user.

## 1. Who the plan is for (`frame`)

| User says | Save |
|---|---|
| "Just me" | `{"family_mode": false}` |
| "Me and my husband, we share everything" | `{"family_mode": true}` |

The quick plan always covers the next 12 months.

## 2. Pay (`incomes`)

Send the amount and the pay period as said. The tool converts to a monthly take-home amount and returns it.

| User says | Save |
|---|---|
| "78k a year, paid every 2 weeks" | `{"incomes": [{"name": "My pay", "amount": 78000, "period": "year", "is_net": false, "kind": "stable"}]}` |
| "I take home $2,380 every two weeks" | `{"incomes": [{"name": "My pay", "amount": 2380, "period": "2weeks", "is_net": true}]}` |
| "About 4,200 a month after tax, and my wife makes 50k before tax with some bonuses" | `{"incomes": [{"name": "My pay", "amount": 4200, "period": "month", "is_net": true}, {"name": "Partner's pay", "amount": 50000, "period": "year", "is_net": false, "kind": "variable"}]}` |
| "I freelance, it can stop for a month or two" | `"kind": "project"` on that income |

- "Every 2 weeks" is how often they are paid; if they give a yearly salary, save the yearly amount with `period: "year"`.
- Pay periods: `week`, `2weeks`, `twice_month`, `month`, `year`.
- Don't ask for a tax rate. For pay before tax the tool uses a typical US rate and shows it; the user can change it.
- Steadiness: `stable` (salary), `variable` (bonuses, some ups and downs), `project` (could stop for a while).

## 3. Spending (`expenses`)

| User says | Save |
|---|---|
| "We spend about 5,500 a month, maybe 600 of that is eating out and fun stuff" | `{"month_total": 5500, "cuttable_month": 600}` |
| "Also an $8,000 down payment on a car next August" | add `"planned": [{"name": "Car down payment", "amount": 8000, "month": <plan month of Aug>}]` |

- `month_total` is everything in a typical month, with yearly costs spread over the months.
- A big cost the user will pay from savings is a planned cost with its month, not a goal. Confirm it back in words:
  "I'll save the $8,000 car as a cost in Aug 2027, paid from savings."

## 4. Savings you can reach (`assets`)

| User says | Save |
|---|---|
| "42k in a high-yield savings at 3.8%, and 5,500 in checking" | `{"cash": [{"name": "High-yield savings", "amount": 42000, "rate": 3.8}, {"name": "Checking", "amount": 5500}]}` |
| "A $5,000 CD at 4.2% that ends in March" | `"deposits": [{"name": "CD", "amount": 5000, "rate": 4.2, "maturity_month": <plan month of Mar>}]` |
| "About $1,800 in SPY" | find the ticker with `search_instruments`, then `"holdings": [{"ticker": "NYSE:SPY", "value": 1800}]` |
| "Some stuff in a trading app, maybe $1,300" | `"holdings": [{"ticker": "OTHER", "name": "Trading app mix", "value": 1300}]` |

- Leave out retirement accounts (401(k), IRA): they are not "savings you can reach" in this plan.
- If the user doesn't know the rate, leave it out: the tool uses the latest national average and shows its date.
- Use tickers exactly as `search_instruments` returns them.

## 5. Cushion and risk (`safety`)

| User says | Save |
|---|---|
| "Six months of bills as an emergency fund, and I could live with a 10% drop" | `{"emergency_months": 6, "max_drawdown_tolerance": 0.1, "allowed_classes": [<the types the user confirmed>]}` |
| "I don't want anything in the stock market" | `"allowed_classes": ["bonds_gov"]` or `[]`, as the user confirms |

- The cushion is months of must-pay bills kept in savings and T-bills, never invested (0 to 12).
- The drop is one of 5%, 10%, 20% or 35% of the invested part.
- `allowed_classes` is required the first time this topic is saved. Types: `equity_us` (S&P 500 index fund, plus any
  companies the user picks in the full questionnaire), `bonds_gov` (bond funds), `gold`. Savings, CDs and T-bills are
  always in. Name the types in plain words, offer the set the step preselects for the drop the user chose, and
  save only what the user confirms. An empty list keeps everything in savings and T-bills.

## 6. Main goal (`goals`)

At most 2 goals in the quick plan.

| User says | Save |
|---|---|
| "I just don't want to lose what I have" | `{"goals": [{"type": "protect_savings", "floor_amount": <amount the user names>}]}` |
| "Have $3,000 set aside for the kids' camp by June" | `{"goals": [{"type": "target_amount", "name": "Kids' camp fund", "amount": 3000, "month": <plan month of Jun>, "priority": "must"}]}` |
| "Get my emergency fund full" | `{"goals": [{"type": "emergency_fund"}]}` |
| "My cash is just sitting there, I want it to beat inflation" | `{"goals": [{"type": "portfolio_return"}]}` |

- "Keep at least": ask for the amount in their words. The tool's default is the savings they can reach minus planned
  costs; say it and let them change it.
- Money they will spend is a planned cost (topic 3), not a goal.
- If they keep a cushion and add no goal, the plan checks the cushion is full by the end.

## 7. Review (`review`)

`get_plan_step` with stage "review" returns the summary to check. It takes no answers. Then `run_plan`.

## Full questionnaire (only when asked)

`start_plan` mode "full": 11 steps with the same first four topics plus surprise costs and cushion (`risks`), a possible
raise or bonus (`upside`, optional), a view of the markets (`market_view`, optional), what the plan may use and up to
10 companies the user picks (`universe`), savings and CD rates and taxes (`deposits_taxes`), and up to 8 goals. The
step text lists every field with its limits and defaults.

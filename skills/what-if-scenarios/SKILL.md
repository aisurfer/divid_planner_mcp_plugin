---
name: what-if-scenarios
description: "Turn \"what if we…\" questions into DIVID Planner changes, compare before and after, and save the version the user chooses."
---

# What-if scenarios

If the DIVID Planner connector is not connected, ask the user to connect it first.

If you haven't said it yet in this conversation, first say: "DIVID Planner is a planning tool that uses AI (Claude) and a simulation model. It's not financial advice, and you make your own decisions."

Use this skill when the user asks "what if…" about a plan they have built: spending less, earning more, a bigger cushion, a smaller or later goal, calmer or bolder investing, more in CDs, adding or taking out savings, or leaving a fund out.

If the user wants to change the plan itself or its answers ("change some parameters in my plan", "edit my answers", "my income changed") rather than try a "what if", open its answers here in the chat: `get_plan_step` with the plan's `plan_id` (from `get_planner_overview`) and stage "review", or the topic they name, then ask what to change. Never send the user to the website to change a plan.

## 1. Find the plan

- Use the run id of the result in this conversation.
- For a saved plan, call `get_planner_overview`, then `get_plan_result` with its plan id (section `overview`); the result gives the plan's run id.
- For a goal change you need the goal's id: `get_plan_result` section `goals` lists them (for example `protect_savings`, `target_1`, `emergency_fund`).
- If there is no plan yet, offer to build one with the `plan-my-year` skill.

## 2. Turn the question into a change

Call `try_what_if` with the run id and the change. Quick changes (`levers`) take a few seconds; edits to the answers (`edits`) take up to 15 seconds.

| The user says | Change to send |
|---|---|
| "What if we spent less on extras / cut eating out by 20%?" | `levers.discretionary_cut_pct`: the percent (0 to 50) |
| "…spent $200 less a month on extras?" | `levers.discretionary_cut_pct`: the $200 as a share of the extras they said they could cut (from section `inputs`), rounded to a whole percent, at most 50. Say which percent you tried |
| "What if I picked up a side job for $500 a month?" | `levers.extra_income_month`: 500 |
| "What if I get a 10% raise?" / "…my pay drops 10%?" | `edits.income_scale`: 1.1 / 0.9 |
| "What if our bills go up 10%?" | `edits.mandatory_scale`: 1.1 |
| "Can we play it calmer?" / "What if I took more ups and downs?" | `levers.risk_level`: `conservative` (calmer), `balanced` (middle) or `growth` (bigger ups and downs, more room to grow) |
| "What if I put some of my spare cash in CDs?" | `levers.cd_share_pct`: the percent |
| "What if the cushion sat in a savings account that pays interest?" | `levers.cushion_in_savings`: true |
| "What if I kept 9 months as a cushion?" | `edits.cushion_months`: 9 |
| "What if the goal were a bit smaller / a bit later?" | `levers.goal_relax`: `{"<goal id>": {"amount_pct": 10}}` (10 or 20), or `{"<goal id>": {"months": 3}}` (3 or 6) |
| "What if I aimed for $10,000 by next June?" | `edits.goals`: `{"<goal id>": {"amount": 10000, "month": <plan month>}}` |
| "What if I add $5,000 to savings now?" / "…take $3,000 out?" | `edits.extra_cash`: 5000 / -3000 |
| "What if I left out gold / a fund / a company?" | `edits.excluded_tickers`: the tickers, as `search_instruments` or the result names them |

- Try one change at a time, unless the user asks for a combination; then send them together in one call.
- Plan months: the plan's month 1 is the month after the market data date; the tool data puts the calendar month next to each one (`month_label`). Say calendar months back ("by Jun 2027"), never the plan month number.
- If the reply says it is still working, call `try_what_if` again with the same run id and the same change.
- If the change isn't in the table (a new planned cost, a new goal type, different pay periods, taxes), say the quick what-if can't test it. Offer to change that answer in the plan instead: `get_plan_step` with the plan's `plan_id` (or its draft id) and that topic, `save_plan_answers`, then `run_plan`. The saved plan stays as it is; saving the new result keeps it too.
- Debts aren't modelled yet: don't turn a debt question into a change. You may say paying down high-interest debt first is a common approach, without numbers.

## 3. Compare before and after

The result gives the change's label and, for each goal, before → after with the likelihood word and %, the typical year-end amount, and, when a goal gets less likely, what holds it back.

- **With the card:** the before → after card shows the rows and has "Use this change" (saves the plan with the change) and "Keep my plan" (saves it as it was, without the change). Don't read the rows back. Say in one or two sentences what the change means for the user's worry or goal, using the tool's numbers.
- **Without a card** (Claude Code, a terminal, some apps, or when no card opens): give the label, then each goal as "before → after" with the tool's words and %, then the typical year end, then the "holds back" line if there is one. Keep it to a few short lines.

Numbers come only from the tool. The before → after pair is the change: say it as the tool gives it ("Typical at year end: before → after"), in summaries too. Never work out a difference, a sum, a percent change or a yearly total yourself ("it adds about $1,200", "$1,200 over a year"); the tool didn't return those numbers. Give each likelihood as the tool's word and % "in the model's simulations", even at 100%, in any language and in summaries too, for example "Keeping at least $14,000: Very high (100%) in the model's simulations". 100% means the goal was met in all or nearly all simulated years; it's still a model estimate, not a promise. Never say "will", "(almost) guaranteed", "certain", "for sure", "risk-free", "safe" or "a sure thing", in any language. Don't state a result as a future fact, in any language and in summaries too ("you'll build the cushion", "you won't reach it"); give the goal with the tool's likelihood word and % instead.

"The model suggests" is fine only for the user's own numbers (spending, income, cushion, CD share, ups and downs, goal amount or date). A split is "the model's split" for their inputs and limits; funds in it are examples. Never tell the user to buy, sell or hold anything, never name a company they didn't pick, and never use "recommend" or "recommendation" about anything.

After a comparison, say: "Nothing is saved until you decide." Offer another change, or to save.

## 4. Save only when the user chooses

- "Use this change" (save the plan with the change): `save_plan` with the run id and the `what_if_id` of the tried change.
- "Keep my plan" (the plan as it was built, without the change): `save_plan` with the run id and no `what_if_id`.
- Use a name if the user gave one. Saving the same plan and change again keeps one copy.
- If the user saved on the card, don't save again; the card already did it.
- After a save, `show_plan` opens the plan again and `get_plan_step` with its `plan_id` changes its answers. `get_plan_link` gives a read-only report on divid.ai, only when the user asks for it.

For "should I buy X?", "is this advice?" or "where do I buy?", call `get_planner_guide` with topic "limits" and use its answers. These are the approved answers; use them word for word:

```text
Q: Is this financial advice?
A: No. It's a planning tool: it shows what the model estimates for the numbers and limits you set, and you make the decisions.

Q: If I lose money, is that on you?
A: Investing always carries risk, and DIVID doesn't manage or trade your money, so any decision and its result are yours. The plan shows the risks, including a very bad year, so you can decide with open eyes.

Q: So should I buy these? / Should I buy X?
A: The plan shows how the model would split your money for your goals. Whether and what to buy is your choice, and you'd do it in your own brokerage account.
(Then explain what the plan shows about X, if anything, with numbers from the tools.)

Q: Is this a robo-advisor?
A: No. A robo-advisor manages your account. DIVID Planner only builds a plan you can read, test and change; it never touches your money.

Q: Where do I buy this?
A: DIVID doesn't sell anything or point you to a place to buy. Any brokerage account you already use can hold funds like these.

Q: What does it cost?
A: It's free during launch.

Q: What happens to my data?
A: Your answers and plans are saved to your DIVID account so you can come back to them. DIVID doesn't see your Claude chat. You can delete plans or your whole account any time: divid.ai/privacy-policy.

Q: Is it good for someone outside the US?
A: It's built for US residents and US dollars. You can still try it, but taxes, products and rules where you live may differ.
```

If X is a company and no plan includes it yet, don't say how it might fit. Say only that the user can add up to 10 companies they pick in the full questionnaire, and the model then only sizes them.

## 5. When a tool says no

- "Build it again" (the plan was built on older market data): offer to rebuild. For a plan built in this conversation, call `run_plan` on its draft; for a saved plan, `run_plan` with the draft id the result gives; only if its answers are no longer kept, `start_plan` with `clone_from_plan_id`, then `run_plan`. Then try the change on the new result.
- "Busy" or a limit reached: pass on the tool's words and wait time. Don't retry in a loop.
- A value out of range: say the allowed range in plain words and ask again.

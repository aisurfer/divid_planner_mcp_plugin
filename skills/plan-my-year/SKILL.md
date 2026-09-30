---
name: plan-my-year
description: "Build a one-year plan for the user's savings with DIVID Planner: quick questions first, rough answers converted and confirmed, then the plan. Use when the user wants a plan for their savings or money this year."
---

# Plan my year

<!-- Skeleton version (0.1.0). The full conversation protocol, examples and references/interview.md follow in a later release. -->

If the DIVID Planner connector is not connected, ask the user to connect it first.

If the user says they are under 18, stop and explain the tool is for adults.

## Steps

1. Call `get_planner_overview`. Once per conversation, before or with the first result, say: "DIVID Planner is a planning tool that uses AI (Claude) and a simulation model. It's not financial advice, and you make your own decisions."
2. Start the quick plan with `start_plan`. Ask one thing at a time in plain words, and use `get_plan_step` to see what comes next.
3. Save each answer with `save_plan_answers`, with its pay period, and confirm it with the monthly amount the tool returns. Don't compute it yourself. If the user gives several answers at once, save them all and continue from the first missing topic.
4. Money the user will spend, such as a down payment, is a planned cost, not a goal.
5. When the answers are complete, call `run_plan`, follow it with `get_plan_run`, then show the result with `show_plan`.
6. Only state numbers the tools returned: dollars first, calendar months. Give each likelihood as the tool's word and % "in the model's simulations", even at 100%, for example "Keeping at least $14,000: Very high (100%) in the model's simulations". Say "likely"; never "will", "guaranteed", "certain", "risk-free", "safe" or "a sure thing", in any language. A likelihood is a model estimate, not a promise. Call every split "the model's split" for the user's own inputs and limits.
7. For "should I buy X?", "is this advice?" or "where do I buy?", call `get_planner_guide` with topic "limits" and use its answers.
8. If a draft stays open, end with: "Your answers are saved. Next time, say 'continue my plan'."

Without cards (for example in a terminal), ask the same questions in text.

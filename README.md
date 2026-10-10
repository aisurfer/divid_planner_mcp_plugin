# DIVID Savings & Investment Planner

DIVID Planner helps you make a plan for the next 12 months for money you've already saved. It's for people in the US who are new to investing and care more about keeping their savings than chasing big gains.

## How it works

Tell Claude about your money in your own words: your take-home pay, what you spend in a month, what you've saved and what you're saving for, like a down payment next fall. Claude fills in the plan from that and asks once for anything it still needs. A card then shows what it read and what it assumed, such as your cushion and how big a drop you could sit through. You can change any of it before the plan is built.

A simulation model then tests the plan against 2,000 possible market years built from real price history. It shows how likely each goal is in plain words, how the model splits your money across the parts you allow, what a very bad year would mean in dollars, and which changes to your own numbers help most. You can try a change, put up to three side by side, save the plan and open it on divid.ai. The model doesn't count debts or their interest.

## Get started

1. Install the plugin. It adds the DIVID Planner connector (`https://mcp.divid.ai/mcp`).
2. Connect it and sign in to DIVID.AI with Google or an email and password. You confirm you're 18 or older.
3. Say: "Help me make a plan for my savings for the next 12 months."

Other things to ask:

- "I have $42,000 in savings and want $8,000 for a car down payment by next summer. Is that realistic without touching our emergency fund?"
- "What happens to my plan if we spend 20% less on extras?"
- "Compare two options for my plan side by side: spending $200 less a month, or adding $300 a month to my pay."
- "Explain my plan in plain words, including what a very bad year would mean in dollars."

Setup help: https://divid.ai/planner/docs

## What's inside

- Skills: `plan-my-year`, `explain-my-plan`, `what-if-scenarios`
- Connector: DIVID Planner, a remote MCP server run by DIVID.AI

## What this plugin sends and stores

The plugin connects to one remote server, `https://mcp.divid.ai/mcp`, operated by DIVID AI TECH LLC. When you use it, Claude sends your planning answers (income, spending, savings, holdings and debts you choose to enter, goals, risk choices) and your plan requests to that server. DIVID stores them in your DIVID account to build and save plans. DIVID doesn't receive your Claude conversation, memory or files. Sign-in happens on `auth.divid.ai`. You can delete plans or your account any time; see https://divid.ai/privacy-policy. The plugin runs no local code and fetches nothing else.

Support: welcome@divid.ai

## Important

DIVID Planner is a self-directed planning and simulation tool, not a financial adviser. It doesn't give personalised investment advice, place trades or move money. Plans are model estimates based on your inputs and historical market data, and results aren't guaranteed. Built for US residents; amounts in USD; 18+. Free during launch. Privacy: https://divid.ai/privacy-policy · Terms: https://divid.ai/terms-and-conditions

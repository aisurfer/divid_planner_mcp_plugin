# DIVID Savings & Investment Planner

DIVID Planner helps you make a plan for the next 12 months for money you've already saved. It's for people who are new to investing and care more about keeping their savings than chasing big gains.

## How it works

Claude asks about six short questions: who the plan is for, your pay, what you spend in a month, your savings, how big a cushion you want, and one goal. You can type in your own words or tap the cards in the chat. A simulation model then tests the plan against 2,000 possible market years and shows how likely each goal is, how the model splits your money, what a very bad year would mean in dollars, and which change helps most. You can try changes, save the plan and open it on divid.ai.

## Get started

1. Install the plugin. It adds the DIVID Planner connector (`https://mcp.divid.ai/mcp`).
2. Sign in to DIVID.AI with Google or an email and password when Claude asks.
3. Say: "Help me make a plan for my savings for the next 12 months."

Setup help: https://divid.ai/planner/docs

## What's inside

- Skills: `plan-my-year`, `explain-my-plan`, `what-if-scenarios`
- Command: `/plan`
- Connector: DIVID Planner, a remote MCP server run by DIVID.AI

## What this plugin sends and stores

The plugin connects to one remote server, `https://mcp.divid.ai/mcp`, operated by DIVID AI TECH LLC. When you use it, Claude sends your planning answers (income, spending, savings, holdings you choose to enter, goals, risk choices) and your plan requests to that server. DIVID stores them in your DIVID account to build and save plans. DIVID doesn't receive your Claude conversation, memory or files. Sign-in happens on `auth.divid.ai`. You can delete plans or your account any time; see https://divid.ai/privacy-policy. The plugin runs no local code and fetches nothing else.

Support: {support_email}

## Important

DIVID Planner is a self-directed planning and simulation tool, not a financial adviser. It doesn't give personalised investment advice, place trades or move money. Plans are model estimates based on your inputs and historical market data, and results aren't guaranteed. Built for US residents; amounts in USD; 18+. Free during launch. Privacy: https://divid.ai/privacy-policy · Terms: https://divid.ai/terms-and-conditions

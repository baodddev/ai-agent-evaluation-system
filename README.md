# AI Agent Evaluation System

An evaluation system for LLM agents, built with [DeepEval](https://github.com/confident-ai/deepeval).
It measures not only whether an agent gives the right final answer, but whether it got there the
right way: calling the right tools, with the right arguments, in a sensible number of steps.

The agent under test is a **customer-support refund agent** (LangChain + Gemini). It is a good
evaluation target because its policy is strict and checkable, so every test case has a clear
expected outcome.

## What gets evaluated

| Metric | Script | Question it answers | Status |
|---|---|---|---|
| Answer correctness | `evaluations/answer_correctness.py` | Does the final answer reach the same conclusion as the expected answer? (GEval) | Ready, needs dataset |
| Tool correctness | `evaluations/tool_correctness.py` | Did the agent call the expected tools? | Ready, needs dataset |
| Argument correctness | `evaluations/argument_correctness.py` | Were the tools called with the right arguments? | In progress |
| Plan quality | `evaluations/plan_quality.py` | Is the agent's plan sound for the task? | In progress |
| Step efficiency | `evaluations/step_efficiency.py` | Did it avoid unnecessary steps? | In progress |
| Task completion | `evaluations/task_completion.py` | Did it finish the task? | In progress |
| Plan adherence | `evaluations/plan_adherence.py` | Did it follow its own plan? | Planned |

Test cases (goldens) go in `evaluations/dataset.py`, and the judge model in `evaluations/model.py`.
Both are still to be written, so no metric can run yet.

## The agent under test

The refund policy is enforced **in code**, not only in the prompt, so the evaluation measures
the agent's reasoning and tool use rather than whether the LLM remembered the rules:

- Purchases older than 30 days, or dated in the future, are rejected.
- Only items the customer actually bought, and asked to return, are refunded.
- An item can't be refunded twice.
- `issue_refund_ticket` recalculates the amount itself, so a prompt like
  "refund me 999999" can't change what gets paid out.

Tools: `get_user_purchase_history`, `calculate_right_refund`, `issue_refund_ticket`, `get_today_date`.

Sample customers in `agent/data.py` cover the edge cases. Dates are relative to today, so the
scenarios stay valid whenever the suite runs:

| User | Item | Bought | Expected |
|---|---|---|---|
| alice | Wireless Mouse / Mechanical Keyboard | 5 / 10 days ago | approve |
| bob | Laptop Stand | 30 days ago | approve (last valid day) |
| bob | USB-C Hub | 31 days ago | reject |
| carol | Monitor | 3 days in the future | reject (invalid date) |

## Running a case without user input

`run_scripted` in `agent/agent.py` runs one case end to end without `input()`. Each call
starts a fresh conversation thread and clears the refund state, so one case can't affect the next.

```python
from agent import run_scripted

state = run_scripted(["Hi, I'm alice. I want to return my Wireless Mouse."])
state["structured_response"].answer        # final answer
state["structured_response"].conversation  # still True = the agent never reached a decision
state["messages"]                          # full trajectory, including tool calls
```

The customer messages are fixed and don't adapt to the agent's questions, so give everything the
agent needs (username and item) in the first message.

## Project layout

```
agent/
  agent.py         agent setup, interactive loop, run_scripted harness
  tools.py         refund tools; policy checks live in check_items()
  prompts.py       system prompt
  data.py          sample customers and purchases
  models.py        LLM config (Gemini)
  objects.py       Answer / PurchaseItem schemas
  test_tools.py    checks for the refund rules (no LLM)
  test_harness.py  checks for run_scripted (stub agent, no LLM)
evaluations/       one DeepEval script per metric
```

## Setup

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.exanple .env   # then set GEMINI_API_KEY
```

The agent is pinned to `gemini-3.6-flash` (not a `-latest` alias), so results stay comparable
between runs. On the Gemini free tier this model allows only about 20 requests per day, and one
case takes 3 to 4 requests, so a real evaluation run needs a paid key.

## Usage

```bash
# checks that don't call the LLM
cd agent
uv run python test_tools.py
uv run python test_harness.py

# talk to the agent yourself
uv run python agent.py

# run an evaluation (once the dataset and judge model are set up), from the repo root
uv run python evaluations/tool_correctness.py
```

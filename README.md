# AI Agent Evaluation System

An evaluation system for LLM agents, built with [DeepEval](https://github.com/confident-ai/deepeval).
It measures not only whether an agent gives the right final answer, but whether it got there the
right way: calling the right tools, with the right arguments, in a sensible number of steps.

The agent under test is a **customer-support refund agent** (LangChain + Gemini). It is a good
evaluation target because its policy is strict and checkable, so every test case has a clear
expected outcome.

## What gets evaluated

| Metric | Script | Question it answers | Status | Latest score | Passed |
|---|---|---|---|---|---|
| Answer correctness | `evaluations/answer_correctness.py` | Does the final answer reach the same conclusion as the expected answer? (GEval) | Working | 1.00 | 3/3 |
| Tool correctness | `evaluations/tool_correctness.py` | Did the agent call the expected tools? | Working | 1.00 | 3/3 |
| Argument correctness | `evaluations/argument_correctness.py` | Were the tools called with the right arguments? | Working | 0.78 | 1/3 |
| Task completion | `evaluations/task_completion.py` | Did it finish the task? | Working | 1.00 | 3/3 |
| Step efficiency | `evaluations/step_efficiency.py` | Did it avoid unnecessary steps? | Working | 0.75 | 1/3 |
| Plan quality | `evaluations/plan_quality.py` | Is the agent's plan sound for the task? | Working | 0.25 | 0/3 |
| Plan adherence | `evaluations/plan_adherence.py` | Did it follow its own plan? | Working | 0.92 | 2/3 |

Scores are from the latest `eval_all.py` run (2026-11-08), averaged over the 3 cases; a case passes at 0.8.
The last four metrics are scored on the trace that DeepEval's `CallbackHandler` records while the
agent runs.

`evaluations/eval_all.py` runs the agent **once** per test case and scores all 7 metrics on that
same run. Running each metric script separately re-runs the agent each time, which costs more
and lets results drift between metrics.

- **Test cases** (`evaluations/dataset.py`): the three alice / bob / carol cases below, each with an
  expected answer and expected tools.
- **Judge** (`evaluations/model.py`): `gemini-3.1-flash-lite`, a different model from the agent, so
  the agent never grades itself.
- **Step limit:** `run_scripted` stops a case after 20 graph steps (a normal case needs about 8).
  A looping agent then fails that case instead of hanging the run and burning quota.

What the failures show:

- **Step efficiency / Plan adherence:** for bob and carol the agent calls `get_today_date` after
  `calculate_right_refund` has already rejected the item, an unneeded extra step. Tool correctness
  misses this because it only checks that the expected tools were called.
- **Argument correctness:** bob and carol score 0.67, so the judge rejected 1 of their 3 calls as
  "missing a required parameter". The only call alice doesn't make is `get_today_date`, which takes
  no parameters, so the judge is likely wrong here. Check the trace before changing the agent.
- **Plan quality:** the judge grades the plan against a generic refund process (return shipping labels,
  attempting the transaction) rather than this policy, so the low score says more about the judge
  than the agent. Passing the policy to the judge would make it meaningful.

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
cp .env.example .env   # then set GEMINI_API_KEY
```

Both models are cheap "lite" models, pinned by exact id (not a `-latest` alias) so results stay
comparable between runs. The agent runs on `gemini-3.5-flash-lite`. `gemini-3.1-flash-lite` was
tried as the agent and looped on tool calls in every case, so it is used only as the judge.

The Gemini free tier allows 5 requests per minute per model, so the agent is throttled to 4 per
minute (`agent/models.py`). A 3-case run takes a few minutes. Remove the throttle once billing is
enabled.

## Usage

```bash
# checks that don't call the LLM
cd agent
uv run python test_tools.py
uv run python test_harness.py

# talk to the agent yourself
uv run python agent.py

# run the evaluation, from the repo root
DEEPEVAL_TELEMETRY_OPT_OUT=YES uv run python evaluations/eval_all.py
```

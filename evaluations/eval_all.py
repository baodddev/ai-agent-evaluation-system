"""Runs the agent once per golden and scores all 7 metrics on that same run.
Cheaper than running each metric script separately, which re-runs the agent for each metric."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from agent import run_scripted
from dataset import dataset
from model import eval_model

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig, CacheConfig
from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import (
    ArgumentCorrectnessMetric, GEval, PlanAdherenceMetric, PlanQualityMetric,
    StepEfficiencyMetric, TaskCompletionMetric, ToolCorrectnessMetric,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall

# Sequential: the judge is on the Gemini free tier too (5 requests/minute).
async_config = AsyncConfig(run_async=False)
cache_config = CacheConfig(write_cache=False)  # cache needs pywin32 on Windows; not needed here

# Scored on the trace that CallbackHandler records while the agent runs.
trace_metrics = [
    TaskCompletionMetric(threshold=0.8, model=eval_model, include_reason=True),
    StepEfficiencyMetric(threshold=0.8, model=eval_model, include_reason=True),
    PlanQualityMetric(threshold=0.8, model=eval_model, include_reason=True),
    PlanAdherenceMetric(threshold=0.8, model=eval_model, include_reason=True),
]

test_cases = []
for golden in dataset.evals_iterator(metrics=trace_metrics, async_config=async_config, cache_config=cache_config):
    # fresh thread + clean refund state + step limit per case
    state = run_scripted([golden.input], callbacks=[CallbackHandler()])
    tools_called = [
        ToolCall(name=tool_call["name"], input_parameters=tool_call["args"])
        for message in state["messages"]
        for tool_call in getattr(message, "tool_calls", []) or []
    ]
    print(f"ran: {golden.input!r} -> tools {[t.name for t in tools_called]}")
    test_cases.append(LLMTestCase(
        input=golden.input,
        actual_output=state["structured_response"].answer,
        expected_output=golden.expected_output,
        tools_called=tools_called,
        expected_tools=golden.expected_tools,
    ))

# Scored on the same runs, from the final answer and the tool calls.
metrics = [
    GEval(
        name="Answer Correctness",
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        evaluation_steps=["make sure that the actual output and the expected output have the same logical conclusion"],
        threshold=0.8,
        model=eval_model,
    ),
    ToolCorrectnessMetric(threshold=0.8, model=eval_model, include_reason=True),
    ArgumentCorrectnessMetric(threshold=0.8, model=eval_model, include_reason=True),
]

evaluate(test_cases=test_cases, metrics=metrics, async_config=async_config, cache_config=cache_config)

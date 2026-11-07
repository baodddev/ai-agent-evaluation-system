import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from agent import run_scripted
from dataset import dataset
from model import eval_model

from deepeval import evaluate
from deepeval.evaluate import AsyncConfig, CacheConfig
from deepeval.metrics import ArgumentCorrectnessMetric
from deepeval.test_case import LLMTestCase, ToolCall

test_cases = []
for golden in dataset.goldens:
    state = run_scripted([golden.input])
    tools_called = [
        ToolCall(name=tool_call["name"], input_parameters=tool_call["args"])
        for message in state["messages"]
        for tool_call in getattr(message, "tool_calls", []) or []
    ]
    test_cases.append(LLMTestCase(
        input=golden.input,
        actual_output=state["structured_response"].answer,
        tools_called=tools_called,
    ))

metrics = [ArgumentCorrectnessMetric(threshold=0.8, model=eval_model, include_reason=True)]

# Sequential: the judge is on the Gemini free tier (5 requests/minute). Cache needs pywin32 on Windows.
evaluate(test_cases=test_cases, metrics=metrics, async_config=AsyncConfig(run_async=False),
         cache_config=CacheConfig(write_cache=False))

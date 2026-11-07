import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))

from agent import run_scripted
from dataset import dataset
from model import eval_model

from deepeval.evaluate import AsyncConfig, CacheConfig
from deepeval.integrations.langchain import CallbackHandler
from deepeval.metrics import PlanQualityMetric

metrics = [PlanQualityMetric(threshold=0.8, model=eval_model, include_reason=True)]

# Scored on the trace CallbackHandler records. Sequential: the judge is on the Gemini free tier (5 requests/minute).
for golden in dataset.evals_iterator(metrics=metrics, async_config=AsyncConfig(run_async=False),
                                     cache_config=CacheConfig(write_cache=False)):  # cache needs pywin32 on Windows
    run_scripted([golden.input], callbacks=[CallbackHandler()])

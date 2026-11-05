import os

from deepeval.models import GeminiModel
from dotenv import load_dotenv

load_dotenv()

# Cheap lite judge, on a different model than the agent (gemini-3.5-flash-lite): a model grading itself is biased.
eval_model = GeminiModel(model="gemini-3.1-flash-lite", api_key=os.getenv("GEMINI_API_KEY"), temperature=0)

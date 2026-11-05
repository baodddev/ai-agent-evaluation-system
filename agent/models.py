from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()
# shortcut: paced for the Gemini free tier (5 requests/minute per model); remove once billing is enabled
rate_limiter = InMemoryRateLimiter(requests_per_second=4 / 60, max_bucket_size=1)
# Reads GEMINI_API_KEY (or GOOGLE_API_KEY). model_provider is required: "gemini-*" alone defaults to Vertex AI.
# Cheap lite model, pinned (not a -latest alias) so eval results stay comparable. gemini-3.1-flash-lite loops on tool calls.
model = init_chat_model(model="gemini-3.5-flash-lite", model_provider="google_genai", rate_limiter=rate_limiter)

# response = model.invoke("what is the capital of VietNam")
# print(response.content)
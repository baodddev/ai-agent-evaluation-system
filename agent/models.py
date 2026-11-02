from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
# Reads GEMINI_API_KEY (or GOOGLE_API_KEY). model_provider is required: "gemini-*" alone defaults to Vertex AI.
# Pinned id (not "gemini-flash-latest") so eval results stay comparable across runs.
model = init_chat_model(model="gemini-3.6-flash", model_provider="google_genai")

# response = model.invoke("what is the capital of VietNam")
# print(response.content)
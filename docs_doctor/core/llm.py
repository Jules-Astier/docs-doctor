from functools import cache
from typing import TypeAlias

from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_community.chat_models import FakeListChatModel
from langchain_ollama.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from docs_doctor.core.settings import settings, OpenRouterModel

@cache
def get_model(model: str) -> ChatOpenAI:
    # NOTE: models with streaming=True will send tokens as they are generated
    # if the /stream endpoint is called with stream_tokens=True (the default)
    print("MODEL: ", model)
    return ChatOpenAI(
        model=model,
        temperature=0.5,
        streaming=True,
        openai_api_base='https://openrouter.ai/api/v1',
        openai_api_key=settings.OPEN_ROUTER_API_KEY,
    )

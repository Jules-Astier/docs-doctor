from functools import cache
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

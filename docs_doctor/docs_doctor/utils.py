"""Utility & helper functions."""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnableConfig

from docs_doctor.core.llm import get_model, settings

def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def call_model(config: RunnableConfig) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    model = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    return model


embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
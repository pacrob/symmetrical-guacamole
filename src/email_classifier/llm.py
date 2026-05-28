import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# from langchain_anthropic import ChatAnthropic

DEFAULT_MODEL = "gpt-4o-mini"
# DEFAULT_MODEL = "claude-haiku-4-5"


def get_chat_model(model: str | None = None) -> BaseChatModel:
    name = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    return ChatOpenAI(model=name, temperature=0)
    # return ChatAnthropic(model=name, temperature=0)

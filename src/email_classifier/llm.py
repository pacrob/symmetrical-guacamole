from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# from langchain_anthropic import ChatAnthropic
from .config import Settings, get_settings


def get_chat_model(settings: Settings | None = None) -> BaseChatModel:
    s = settings or get_settings()
    return ChatOpenAI(
        model=s.llm_model,
        temperature=0,
        api_key=s.openai_api_key,
    )
    # return ChatAnthropic(
    #     model=s.llm_model,
    #     temperature=0,
    #     api_key=s.anthropic_api_key,
    # )

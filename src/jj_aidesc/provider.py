from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from jj_aidesc.config import Config


class Provider(Protocol):
    name: str
    model_name: str
    chat_model: BaseChatModel


class GoogleGenAIProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
    ):
        self.name: str = "google-genai"
        self.model_name: str = model
        self.temperature: float = temperature
        self._api_key: str = api_key
        self.chat_model: BaseChatModel = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )


def get_provider(config: Config) -> Provider:
    return GoogleGenAIProvider(
        api_key=config.api_key,
        model=config.model,
        temperature=config.temperature,
    )

import socket
from typing import Annotated, Any

from dotenv import find_dotenv
from pydantic import BeforeValidator, HttpUrl, SecretStr, TypeAdapter, computed_field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

import requests
from src.utils.multiprocessing import parallel_execute
def check_model_tools(model):
    try:
        endpoints = requests.get(f"https://openrouter.ai/api/v1/models/{model['id']}/endpoints").json()['data']['endpoints']
        for endpoint in endpoints:
            if "tools" in endpoint['supported_parameters']:
                return model
    except Exception as e:
        print(f"Error checking {model['id']}: {e}")
    return None

def list_tools_models():
        models = requests.get("https://openrouter.ai/api/v1/models").json()['data']
        tool_models = [model for model in parallel_execute(check_model_tools, [{"model": model} for model in models]) if model]
        return tool_models
def check_str_is_http(x: str) -> str:
    http_url_adapter = TypeAdapter(HttpUrl)
    return str(http_url_adapter.validate_python(x))

class OpenRouterArch(BaseModel):
    modality: str
    tokenizer: str
    instruct_type: str

class OpenRouterPricing(BaseModel):
    prompt: float
    completion: float
    image: float
    request: float

class OpenRouterModel(BaseModel):
    id: str
    name: str
    created: int
    description: str
    context_length: int
    architecture: OpenRouterArch
    pricing: OpenRouterPricing

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_dotenv(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        validate_default=False,
    )
    MODE: str | None = None

    HOST: str = "localhost"
    PORT: int = 8000

    OPEN_ROUTER_API_KEY: SecretStr

    DEFAULT_MODEL: OpenRouterModel | None = None  # type: ignore[assignment]
    AVAILABLE_MODELS: list[OpenRouterModel] = list()  # type: ignore[assignment]

    DEFAULT_STREAMING: bool | None = True

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "default"
    LANGCHAIN_ENDPOINT: Annotated[str, BeforeValidator(check_str_is_http)] = (
        "https://api.smith.langchain.com"
    )
    LANGCHAIN_API_KEY: SecretStr | None = None

    def check_ollama_service_sync(self):
        """
        Synchronous version to check if Ollama service is running on port 11434.
        Returns tuple of (bool, str) indicating status and message.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex(('localhost', self.OLLAMA_PORT))
            return result == 0
        except socket.error:
            return False
        finally:
            sock.close()


    def model_post_init(self, __context: Any) -> None:
        self.AVAILABLE_MODELS = list_tools_models()
        self.DEFAULT_MODEL = self.AVAILABLE_MODELS[0]

    @computed_field
    @property
    def BASE_URL(self) -> str:
        return f"http://{self.HOST}:{self.PORT}"

    def is_dev(self) -> bool:
        return self.MODE == "dev"


settings = Settings()

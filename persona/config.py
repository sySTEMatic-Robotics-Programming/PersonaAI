# PersonaAI - config.py
#
# Settings. Everything comes from environment variables or a .env file, so
# no keys end up in the code.

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass


def _list(value: str) -> list[str]:
    return [v.strip().lower() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    name: str = os.getenv("PERSONA_NAME", "PersonaAI")
    wake_words: list[str] = field(default_factory=lambda: _list(os.getenv("PERSONA_WAKE_WORDS", "hello")))
    sleep_words: list[str] = field(default_factory=lambda: ["goodbye"])
    stop_words: list[str] = field(default_factory=lambda: ["stop"])
    quit_words: list[str] = field(default_factory=lambda: ["quit"])

    hardware: str = os.getenv("PERSONA_HARDWARE", "sim")
    tracking: bool = os.getenv("PERSONA_TRACKING", "0") == "1"

    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_model: str = os.getenv("LLM_MODEL", "")

    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")

    # past exchanges to remember
    history_turns: int = int(os.getenv("PERSONA_HISTORY_TURNS", "10"))

    # simple default persona
    system_prompt: str = os.getenv(
        "PERSONA_SYSTEM_PROMPT",
        "You are {name}, a friendly robot assistant. Answer briefly, in plain "
        "spoken sentences, in the same language the user used.",
    )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key and self.llm_model)


settings = Settings()

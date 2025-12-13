"""Configuration management."""

import os
import subprocess
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import dotenv_values

from jj_aidesc.error import ConfigError

ENV_FILES = [".env", ".env.local"]
CONFIG_FILES = [".jj-aidesc.yaml", ".jj-aidesc.yml"]
API_KEY_ENV_VAR = "GOOGLE_GENAI_API_KEY"

CONFIG_TEMPLATE = f"""\
# jj-aidesc configuration file
# See https://github.com/suda-3156/jj-aidesc for more information

google-genai:
  # Google GenAI API key (can also be set via {API_KEY_ENV_VAR} env var)
  # api_key: "your-api-key-here"

  # Model to use for generation
  model: "gemini-2.5-flash"

  # Temperature for generation (0.0 - 1.0)
  temperature: 0.0

  # Language for commit messages
  language: English

  # Style: conventional, follow, simple
  style: conventional
"""


def _get_jj_root_dir() -> Path | None:
    try:
        result = subprocess.run(
            ["jj", "root"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _get_search_dirs() -> list[Path]:
    dirs = [Path.cwd()]
    jj_root = _get_jj_root_dir()
    if jj_root and jj_root != Path.cwd():
        dirs.append(jj_root)
    return dirs


@dataclass
class Config:
    _model: str | None
    _temperature: float | None
    _api_key: str | None
    _config_path: str | None
    _language: str | None
    _style: str | None

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ConfigError(
                f"No API key found. Set via --api-key, config file, "
                f".env, or {API_KEY_ENV_VAR} environment variable."
            )

    @cached_property
    def _config(self) -> dict[str, Any] | None:
        # Explicit config path
        if self._config_path:
            config_path = Path(self._config_path)
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f)
            raise ConfigError(f"Config file not found: {self._config_path}")

        # Search in cwd and jj root directory
        for search_dir in _get_search_dirs():
            for config_file in CONFIG_FILES:
                config_path = search_dir / config_file
                if config_path.exists():
                    with open(config_path) as f:
                        return yaml.safe_load(f)

        return None

    def _from_config(self, key: str) -> Any | None:
        if self._config and "google-genai" in self._config:
            return self._config["google-genai"].get(key)
        return None

    @property
    def api_key(self) -> str:
        # 1. CLI option
        if self._api_key:
            return self._api_key

        # 2. Config file
        if key := self._from_config("api_key"):
            return str(key)

        # 3. .env file (search cwd and jj root)
        for search_dir in _get_search_dirs():
            for env_file in ENV_FILES:
                env_path = search_dir / env_file
                if env_path.exists():
                    env_values = dotenv_values(env_path)
                    if key := env_values.get(API_KEY_ENV_VAR):
                        return key

        # 4. Environment variable
        return os.getenv(API_KEY_ENV_VAR, "")

    @property
    def model(self) -> Optional[str]:
        return self._model or self._from_config("model")

    @property
    def temperature(self) -> float:
        if self._temperature is not None:
            return self._temperature
        config_temp = self._from_config("temperature")
        if config_temp is not None:
            return float(config_temp)
        return 0.0

    @property
    def language(self) -> str:
        lang = self._language or self._from_config("language") or "English"
        # Convert language code to full name
        lang_map = {
            "en": "English",
            "ja": "Japanese",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ko": "Korean",
        }
        return lang_map.get(lang.lower(), lang)

    @property
    def style(self) -> str:
        return self._style or self._from_config("style") or "conventional"

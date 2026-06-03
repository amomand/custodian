from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Config:
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    openai_reasoning_effort: str = "none"
    custodian_ai: bool = True


def load_config(env_path: Path | None = None) -> Config:
    if env_path is None:
        env_path = _repo_root() / ".env"
    _load_dotenv(env_path)

    return Config(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        openai_reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "none"),
        custodian_ai=os.getenv("CUSTODIAN_AI", "on").strip().lower()
        not in {"0", "false", "no", "off"},
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    pushplus_token: str
    pushplus_channel: str
    lookback_hours: int
    max_per_source: int
    top_n: int
    timeout_seconds: int

    @classmethod
    def from_env(cls, require_secrets: bool = True) -> "Settings":
        api_key = os.getenv("AI_API_KEY", "").strip()
        token = os.getenv("PUSHPLUS_TOKEN", "").strip()
        if require_secrets:
            missing = [
                name
                for name, value in (("AI_API_KEY", api_key), ("PUSHPLUS_TOKEN", token))
                if not value
            ]
            if missing:
                raise RuntimeError(f"缺少必需环境变量：{', '.join(missing)}")

        return cls(
            api_key=api_key,
            base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            model=os.getenv("AI_MODEL", "gpt-5.4-mini"),
            pushplus_token=token,
            pushplus_channel=os.getenv("PUSHPLUS_CHANNEL", "wechat").strip() or "wechat",
            lookback_hours=_positive_int("NEWS_LOOKBACK_HOURS", 48),
            max_per_source=_positive_int("MAX_PER_SOURCE", 8),
            top_n=_positive_int("TOP_N", 7),
            timeout_seconds=_positive_int("REQUEST_TIMEOUT_SECONDS", 30),
        )


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} 必须是整数") from exc
    if value <= 0:
        raise RuntimeError(f"{name} 必须大于 0")
    return value

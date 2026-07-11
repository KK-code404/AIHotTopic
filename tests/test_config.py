import pytest

from ai_daily.config import Settings


def test_dry_run_does_not_require_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("PUSHPLUS_TOKEN", raising=False)
    settings = Settings.from_env(require_secrets=False)
    assert settings.lookback_hours == 48
    assert settings.top_n == 7


def test_normal_run_requires_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("PUSHPLUS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="AI_API_KEY"):
        Settings.from_env()

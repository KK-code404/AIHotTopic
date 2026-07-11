from __future__ import annotations

import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(("GET", "POST")),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def markdown_to_chat_text(content: str) -> str:
    text = re.sub(r"\[([^]]+)]\((https?://[^)]+)\)", r"\1：\2", content)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^(##\s+\d{2}｜)", r"---\n\1", text)
    text = re.sub(r"(?m)^(##\s+🔭\s*今日观察)", r"---\n\1", text)
    sections = [part.strip() for part in re.split(r"(?m)^---+\s*$", text) if part.strip()]
    rendered: list[str] = []

    for index, section in enumerate(sections):
        lines = [
            re.sub(r"^>\s?", "", line).strip()
            for line in section.splitlines()
            if line.strip()
        ]
        if not lines:
            continue

        if index == 0 and lines[0].startswith("# "):
            title = re.sub(r"^#\s+", "", lines[0])
            subtitle = "\n".join(lines[1:])
            rendered.append(
                "╭━━━━━━━━━━━━━━╮\n"
                f"　{title}\n"
                "╰━━━━━━━━━━━━━━╯"
                + (f"\n{subtitle}" if subtitle else "")
            )
            continue

        heading = re.sub(r"^#{1,6}\s*", "", lines[0])
        if re.match(r"^\d{2}｜", heading):
            body = [re.sub(r"^#{1,6}\s*", "", line) for line in lines[1:]]
            decorated: list[str] = [f"┏━ {heading}"]
            for line in body:
                if "　" in line and not line.startswith(("💡", "⚡", "🔗")):
                    line = "🏷 " + line.replace("　", " · ")
                elif line == "一句话速览":
                    line = "⚡ 一句话速览"
                decorated.append(f"┃ {line}")
            decorated.append("┗━━━━━━━━━━━━━━")
            rendered.append("\n".join(decorated))
            continue

        clean_lines = [re.sub(r"^#{1,6}\s*", "", line) for line in lines]
        rendered.append(
            "╭─ 🔭 今日观察 ──────\n"
            + "\n".join(f"│ {line}" for line in clean_lines[1:] or clean_lines)
            + "\n╰━━━━━━━━━━━━━━"
        )

    return "\n\n".join(rendered).strip()


def push_to_wechat(
    token: str, title: str, content: str, timeout: int, channel: str = "clawbot"
) -> None:
    is_clawbot = channel == "clawbot"
    response = create_session().post(
        "https://www.pushplus.plus/send",
        json={
            "token": token,
            "title": title,
            "content": markdown_to_chat_text(content) if is_clawbot else content,
            "template": "txt" if is_clawbot else "markdown",
            "channel": channel,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError("PushPlus 返回了无效 JSON") from exc
    if result.get("code") != 200:
        raise RuntimeError(f"PushPlus 推送失败：{result}")

from __future__ import annotations

import hashlib
import html
import json
import re
from calendar import timegm
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class Article:
    source: str
    title: str
    summary: str
    link: str
    published: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def load_sources(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("sources.json 必须是非空数组")
    for source in data:
        if not isinstance(source, dict) or not source.get("name") or not source.get("url"):
            raise ValueError("每个新闻源必须包含 name 和 url")
    return data


def fetch_news(
    sources: list[dict[str, str]],
    max_per_source: int,
    lookback_hours: int,
    timeout_seconds: int = 30,
) -> list[Article]:
    now = datetime.now(timezone.utc)
    articles: list[Article] = []
    failures: list[str] = []
    session = _create_session()

    for source in sources:
        source_lookback = int(source.get("lookback_hours", lookback_hours))
        cutoff = now - timedelta(hours=source_lookback)
        try:
            response = session.get(source["url"], timeout=timeout_seconds)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except (requests.RequestException, ValueError) as exc:
            failures.append(f"{source['name']}: {exc}")
            continue
        if getattr(feed, "bozo", False) and not feed.entries:
            failures.append(f"{source['name']}: {feed.bozo_exception}")
            continue
        for entry in feed.entries[:max_per_source]:
            published_dt = _entry_datetime(entry)
            if published_dt and published_dt < cutoff:
                continue
            title = _clean_text(entry.get("title", ""))
            link = _canonical_url(entry.get("link", ""))
            if not title or not link:
                continue
            articles.append(
                Article(
                    source=source["name"],
                    title=title,
                    summary=_clean_text(entry.get("summary", ""))[:1200],
                    link=link,
                    published=published_dt.isoformat() if published_dt else "",
                )
            )

    if failures:
        print("部分新闻源读取失败：" + " | ".join(failures))
    return deduplicate(articles)


def _create_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(("GET",)),
    )
    session = requests.Session()
    session.headers["User-Agent"] = "AI-Daily-Push/1.0 (+RSS reader)"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def deduplicate(articles: list[Article]) -> list[Article]:
    seen: set[str] = set()
    result: list[Article] = []
    for article in articles:
        normalized_title = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", article.title.lower())
        key = hashlib.sha256(f"{normalized_title}|{article.link}".encode()).hexdigest()
        title_key = hashlib.sha256(normalized_title.encode()).hexdigest()
        if key in seen or title_key in seen:
            continue
        seen.update((key, title_key))
        result.append(article)
    return sorted(result, key=lambda item: item.published, reverse=True)


def _entry_datetime(entry: dict) -> datetime | None:
    value = entry.get("published_parsed") or entry.get("updated_parsed")
    if not value:
        return None
    return datetime.fromtimestamp(timegm(value), tz=timezone.utc)


def _clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", without_tags).strip()


def _canonical_url(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    except ValueError:
        return value.strip()

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import Settings
from .news import fetch_news, load_sources
from .push import push_to_wechat
from .report import generate_report


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="抓取、总结并推送每日 AI 热点")
    parser.add_argument("--dry-run", action="store_true", help="只抓取并输出候选新闻")
    parser.add_argument("--no-push", action="store_true", help="生成日报但不推送")
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    args = parser.parse_args()

    settings = Settings.from_env(require_secrets=not args.dry_run)
    sources = load_sources(args.sources)
    articles = fetch_news(
        sources,
        settings.max_per_source,
        settings.lookback_hours,
        settings.timeout_seconds,
    )
    if not articles:
        raise RuntimeError("指定时间窗口内没有获取到任何 AI 新闻")

    print(f"获取并去重后共有 {len(articles)} 条候选新闻")
    if args.dry_run:
        print(json.dumps([item.as_dict() for item in articles], ensure_ascii=False, indent=2))
        return

    china_standard_time = timezone(timedelta(hours=8), name="Asia/Shanghai")
    today = datetime.now(china_standard_time).strftime("%Y-%m-%d")
    report = generate_report(
        articles,
        settings.api_key,
        settings.base_url,
        settings.model,
        settings.top_n,
        today,
    )
    if args.no_push:
        print(report)
        return

    push_to_wechat(
        settings.pushplus_token,
        f"AI 热点日报｜{today}",
        report,
        settings.timeout_seconds,
        settings.pushplus_channel,
    )
    print("AI 热点日报推送成功")

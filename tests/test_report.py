from ai_daily.news import Article
from ai_daily.report import build_prompt


def test_prompt_contains_mobile_markdown_layout() -> None:
    article = Article(
        source="OpenAI",
        title="Example",
        summary="Summary",
        link="https://example.test/news",
        published="2026-07-11T00:00:00+00:00",
    )
    prompt = build_prompt([article], 5, "2026-07-11")

    assert "# 🤖 AI 热点日报" in prompt
    assert "## 01｜中文新闻标题" in prompt
    assert "💡 **为什么重要**" in prompt
    assert "[🔗 阅读原文]" in prompt
    assert "2026-07-11" in prompt
    assert article.link in prompt
    assert "Salesforce News" in prompt

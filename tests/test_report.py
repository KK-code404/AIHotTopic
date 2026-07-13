from ai_daily.news import Article
from ai_daily.report import build_prompt, enforce_source_order


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
    assert "绝对不得超过 2 条" in prompt
    assert "先输出 5 至 6 条" in prompt
    assert "必须连续放在整份新闻列表的最后" in prompt


def test_salesforce_cards_are_capped_and_moved_to_end() -> None:
    content = """# 🤖 AI 热点日报
---
## 01｜Salesforce first
`产品更新`　`Salesforce News`
---
## 02｜General AI
`模型发布`　`OpenAI`
---
## 03｜Salesforce second
`产业动态`　`Salesforce Agentforce`
---
## 04｜Salesforce extra
`产业动态`　`Salesforce News`
---
## 🔭 今日观察
> observation
"""
    result = enforce_source_order(content)

    assert result.index("General AI") < result.index("Salesforce first")
    assert result.index("Salesforce first") < result.index("Salesforce second")
    assert "Salesforce extra" not in result
    assert "## 01｜General AI" in result
    assert "## 02｜Salesforce first" in result
    assert "## 03｜Salesforce second" in result

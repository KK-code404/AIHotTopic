from ai_daily.push import markdown_to_chat_text


def test_markdown_to_chat_text_removes_markup_and_keeps_link() -> None:
    markdown = """# 🤖 AI 热点日报

> 📅 2026-07-11

## 01｜模型发布

`模型发布`　`OpenAI`

💡 **为什么重要**

[🔗 阅读原文](https://example.test/news)

---
"""
    text = markdown_to_chat_text(markdown)

    assert "#" not in text
    assert "**" not in text
    assert "`" not in text
    assert "🔗 阅读原文：https://example.test/news" in text
    assert "🤖 AI 热点日报" in text
    assert "╭━━━━━━━━━━━━━━╮" in text
    assert "┏━ 01｜模型发布" in text
    assert "┗━━━━━━━━━━━━━━" in text

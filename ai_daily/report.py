from __future__ import annotations

import json

from openai import OpenAI

from .news import Article


def build_prompt(articles: list[Article], top_n: int, report_date: str) -> str:
    candidates = json.dumps([item.as_dict() for item in articles], ensure_ascii=False)
    return f"""你是一名严谨、克制且有审美的中文 AI 行业资讯编辑。
请仅依据候选新闻，生成一份适合微信手机端阅读的 Markdown 日报，筛选最重要的 {top_n} 条；不足时不要凑数。

内容规则：
- 合并重复事件，优先模型发布、产品重大更新、开发者生态、监管政策和重要融资。
- 排除纯营销、普通教程和缺乏实质内容的文章，不得补充候选数据中没有的事实。
- 如果候选中存在有实质内容的 Salesforce News 或 Salesforce Agentforce 新闻，优先选入 1 至 2 条；不要为了配额选入纯营销内容。
- 标题和摘要使用自然、准确的中文；公司名、产品名和模型名保留官方写法。
- 链接必须逐字使用候选新闻中的 link，不得修改或杜撰。

严格使用下面的版式，不要输出代码围栏，也不要增加格式之外的字段：

# 🤖 AI 热点日报

> 📅 {report_date}　·　为你精选今日最值得关注的 AI 动态

---

## 01｜中文新闻标题

`类别标签`　`来源名称`

**一句话速览**

用 1 至 2 句清楚说明发生了什么。

💡 **为什么重要**

用 1 句说明对产品、开发者、企业或行业的实际影响。

[🔗 阅读原文](候选新闻中的原始链接)

---

后续新闻继续使用 02、03 等两位编号和相同结构，每条之间保留分隔线。类别标签从“模型发布、产品更新、开发者、产业动态、政策治理、投融资、研究进展”中选择一个。

全部新闻之后，以如下格式结尾：

## 🔭 今日观察

> 不超过 80 个汉字的趋势判断，只能基于上述候选新闻，不得夸大。

候选新闻 JSON：
{candidates}
"""


def generate_report(
    articles: list[Article],
    api_key: str,
    base_url: str,
    model: str,
    top_n: int,
    report_date: str,
) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=60, max_retries=3)
    response = client.responses.create(
        model=model,
        instructions=(
            "你只能根据用户提供的候选新闻制作准确的中文日报。"
            "严格遵守用户指定的 Markdown 版式，链接必须来自候选数据。"
        ),
        input=build_prompt(articles, top_n, report_date),
    )
    content = response.output_text.strip()
    if not content:
        raise RuntimeError("模型返回了空日报")
    return content

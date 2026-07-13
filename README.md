# AI 热点推送机器人

每天从官方 RSS 抓取 AI 新闻，去重后调用 OpenAI Responses API 生成中文日报，并通过 PushPlus 推送到微信。项目可在本地、Docker 或 Harness CI 中运行。

## 快速开始

要求 Python 3.11+（推荐 3.12）。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

将 `.env` 中的值配置到当前终端（程序不会自动读取 `.env`）：

```powershell
$env:AI_API_KEY="sk-..."
$env:AI_MODEL="gpt-5.4-mini"
$env:PUSHPLUS_TOKEN="..."
python main.py
```

先测试 RSS，无需任何密钥：

```powershell
python main.py --dry-run
```

生成日报但不推送：

```powershell
python main.py --no-push
```

运行测试：

```powershell
pytest -q
```

## 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|---|---:|---|---|
| `AI_API_KEY` | 是 | - | OpenAI API Key |
| `AI_BASE_URL` | 否 | `https://api.openai.com/v1` | 兼容接口地址 |
| `AI_MODEL` | 否 | `gpt-5.4-mini` | 日报总结模型 |
| `PUSHPLUS_TOKEN` | 是 | - | PushPlus Token |
| `PUSHPLUS_CHANNEL` | 否 | `wechat` | 自动日报使用稳定的公众号通道；手动好友式测试可设为 `clawbot` |
| `NEWS_LOOKBACK_HOURS` | 否 | `48` | 新闻时间窗口 |
| `MAX_PER_SOURCE` | 否 | `8` | 每个源最多读取数 |
| `TOP_N` | 否 | `7` | 日报目标条数 |
| `REQUEST_TIMEOUT_SECONDS` | 否 | `30` | PushPlus 超时秒数 |

新闻源在 `sources.json` 中维护。某个源失败不会阻止其他源继续处理。

默认日报共 7 条：前面 5–6 条为综合 AI 热点，最后 1–2 条为 Salesforce News 或 Salesforce Agentforce。程序会自动重排并限制 Salesforce 最多 2 条。

## Harness 部署

1. 将仓库推送到 GitHub/GitLab，并在 Harness 建立代码仓库 Connector。
2. 在 Project Secrets 创建四个 Text Secret：`ai_api_key`、`ai_base_url`、`ai_model`、`pushplus_token`。
3. 导入 `harness/pipeline.yaml`，填写组织、项目、仓库 Connector 和仓库名称输入。
4. 首次手动运行 Pipeline，确认测试、抓取、模型总结和微信推送均成功。
5. 在 Pipeline 的 **Triggers → New Trigger → Cron** 中导入或按 `harness/trigger.yaml` 配置。

Trigger 使用 `0 1 * * *`，即 UTC 每天 01:00，对应北京时间每天 09:00。若账户已启用 Harness 多时区 Cron 功能，也可在界面直接选 `Asia/Shanghai` 并改为 `0 9 * * *`。

Harness YAML 的 `projectIdentifier`、`orgIdentifier`、代码库 `connectorRef` 和 `repoName` 与账户相关，因此保留为运行时输入。若导入 Trigger YAML 时平台要求固定标识符，请在 Harness UI 中用实际值替换 `<+input>`。

## GitHub Actions 自动补发

`.github/workflows/daily.yml` 使用三次云端检查：北京时间 09:07 首次发送，09:27 和 09:47 作为看门狗补发。首次发送成功后会为当天保存 delivery marker，后续检查发现标记后自动跳过；如果任务未触发或中途失败，没有成功标记，下一次检查会重新发送。

该机制确认的是 GitHub 工作流与 PushPlus API 请求成功。云端自动日报默认使用无需每日激活的 `wechat` 公众号通道；如手动改用 ClawBot，每 24 小时以及每收到 10 次推送后，需要主动向 ClawBot 发送一条消息。

## Docker

```powershell
docker build -t ai-daily-push .
docker run --rm `
  -e AI_API_KEY=$env:AI_API_KEY `
  -e AI_MODEL=gpt-5.4-mini `
  -e PUSHPLUS_TOKEN=$env:PUSHPLUS_TOKEN `
  ai-daily-push
```

## 安全说明

- 不要提交 `.env`、API Key 或 PushPlus Token。
- Harness 中只通过 Secret 表达式注入密钥。
- 正式运行前先使用 `--dry-run` 检查 RSS，再用 `--no-push` 检查日报内容。

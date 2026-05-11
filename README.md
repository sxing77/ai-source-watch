# AI Source Watch

定时监控两个来源的新内容：

- Replicate 新模型：使用官方 API。
- Toolify 新 AI 工具：优先直接抓取 `https://www.toolify.ai/zh/new`，被 Cloudflare 挡住时用 Playwright 渲染兜底。

状态保存在 `data/seen.sqlite`，报告默认写到 `reports/latest.md`。这很适合让 OpenClaw 定时运行，然后读取报告做摘要或通知。

## 安装

```powershell
cd D:\giteeWorkspace\ai-source-watch
.\setup.ps1
copy .env.example .env
```

编辑 `.env`，填入：

```dotenv
REPLICATE_API_TOKEN=你的 Replicate API Token
```

## 第一次建立基线

第一次建议先建立基线，避免把当前页面上的几十个工具都当作“新增”推送：

```powershell
cd D:\giteeWorkspace\ai-source-watch
.\.venv\Scripts\python.exe -m ai_source_watch --bootstrap
```

## 日常运行

```powershell
cd D:\giteeWorkspace\ai-source-watch
.\.venv\Scripts\python.exe -m ai_source_watch --output reports/latest.md
```

如果没有新增，报告里会出现 `NO_NEW_ITEMS`。

## 给 OpenClaw 的任务提示

可以让 OpenClaw 定时执行：

```text
进入 D:\giteeWorkspace\ai-source-watch，运行：
.\.venv\Scripts\python.exe -m ai_source_watch --output reports/latest.md

然后读取 reports/latest.md：
- 如果包含 NO_NEW_ITEMS，只回复“今天没有发现新增 AI 模型或工具”。
- 如果有新增，按来源分组，用中文总结名称、链接、简介。
- 如果报告里有“注意”，把注意事项也告诉我。
```

## 常用参数

```powershell
# 只查 Toolify
.\.venv\Scripts\python.exe -m ai_source_watch --skip-replicate

# 只查 Replicate
.\.venv\Scripts\python.exe -m ai_source_watch --skip-toolify

# 输出 JSON
.\.venv\Scripts\python.exe -m ai_source_watch --format json --output reports/latest.json

# Toolify 不使用浏览器兜底
.\.venv\Scripts\python.exe -m ai_source_watch --no-browser
```

## 备注

Replicate API 通常需要 token。Toolify 有 Cloudflare 防护，HTTP 抓取可能失败；脚本已经内置 Playwright 兜底，但如果目标环境不能运行浏览器，报告会把失败原因写出来。

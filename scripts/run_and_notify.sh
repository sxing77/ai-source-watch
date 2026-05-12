#!/bin/bash
# AI Source Watch - 完整运行脚本
# 1. 运行监控
# 2. 生成 JSON
# 3. 发送邮件（如果有新增）

set -e

cd /root/.openclaw/workspace/ai-source-watch
source .venv/bin/activate

echo "🤖 开始运行 AI Source Watch..."

# 1. 运行监控
python -m ai_source_watch --output reports/latest.md

# 2. 生成 JSON 数据
python scripts/generate_json.py

# 3. 检查是否有新增，有则发送邮件
if grep -q "新增数量：0" reports/latest.md; then
    echo "📭 今日无新增，跳过邮件"
else
    echo "📧 发现新增，发送邮件..."
    python scripts/send_email.py reports/latest.md || echo "邮件发送失败（可能需要配置 SMTP_PASSWORD）"
fi

echo "✅ 运行完成"

#!/bin/bash
# AI Source Watch - 运行并发送飞书通知

set -e

cd /root/.openclaw/workspace/ai-source-watch
source .venv/bin/activate

echo "🤖 [$(date '+%Y-%m-%d %H:%M:%S')] 开始运行 AI Source Watch..."

# 运行监控
python -m ai_source_watch --output reports/latest.md

# 生成 JSON 数据
python scripts/generate_json.py

# 读取结果
NEW_COUNT=$(grep "新增数量：" reports/latest.md | sed 's/.*新增数量：//' | tr -d ' ')
if [ -z "$NEW_COUNT" ]; then
    NEW_COUNT=0
fi

# 发送飞书通知
curl -s -X POST "https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址" \
    -H "Content-Type: application/json" \
    -d "{
        \"msg_type\": \"text\",
        \"content\": {
            \"text\": \"🤖 AI新品监控完成\\n📅 $(date '+%Y-%m-%d %H:%M:%S')\\n📦 新增数量：$NEW_COUNT\\n🔗 查看面板：http://107.161.89.207:8081/ai-watch/\"
        }
    }" > /dev/null 2>&1 || echo "飞书通知发送失败（可能没有配置webhook）"

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 运行完成，新增: $NEW_COUNT"

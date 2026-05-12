#!/bin/bash
# AI Source Watch - 运行并创建飞书通知标记

set -e

cd /root/.openclaw/workspace/ai-source-watch
source .venv/bin/activate

echo "🤖 [$(date '+%Y-%m-%d %H:%M:%S')] 开始运行 AI Source Watch..."

# 运行监控
python -m ai_source_watch --output reports/latest.md

# 生成 JSON 数据
python scripts/generate_json.py

# 检查是否有新增
NEW_COUNT=$(grep "新增数量：" reports/latest.md | sed 's/.*新增数量：//' | tr -d ' ')
if [ -z "$NEW_COUNT" ]; then
    NEW_COUNT=0
fi

echo "✅ [$(date '+%Y-%m-%d %H:%M:%S')] 运行完成，新增: $NEW_COUNT"

# 如果有新增，创建飞书通知标记文件
if [ "$NEW_COUNT" -gt 0 ]; then
    # 读取新模型详情
    MODELS=$(grep -A2 "^## Replicate" reports/latest.md | head -20 || echo "")
    
    cat > /tmp/ai-watch-notify.json << EOF
{
    "type": "ai-watch-new-items",
    "timestamp": "$(date -Iseconds)",
    "new_count": $NEW_COUNT,
    "message": "🤖 AI新品监控完成\\n📅 $(date '+%Y-%m-%d %H:%M')\\n📦 新增 $NEW_COUNT 个模型"
}
EOF
    echo "📢 已创建通知标记: $NEW_COUNT 个新增"
else
    # 无新增时也创建标记（用于确认运行完成）
    cat > /tmp/ai-watch-notify.json << EOF
{
    "type": "ai-watch-no-new",
    "timestamp": "$(date -Iseconds)",
    "new_count": 0,
    "message": "🤖 AI新品监控完成\\n📅 $(date '+%Y-%m-%d %H:%M')\\n📭 今日无新增"
}
EOF
    echo "📭 今日无新增"
fi

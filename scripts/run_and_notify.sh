#!/bin/bash
# AI Source Watch - 运行并直接发送飞书通知

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

# 构建飞书消息
if [ "$NEW_COUNT" -gt 0 ]; then
    MESSAGE="🤖 AI新品监控完成\n📅 $(date '+%Y-%m-%d %H:%M')\n📦 新增 $NEW_COUNT 个模型\n🔗 查看面板：http://107.161.89.207:8081/ai-watch/"
else
    MESSAGE="🤖 AI新品监控完成\n📅 $(date '+%Y-%m-%d %H:%M')\n📭 今日无新增\n🔗 查看面板：http://107.161.89.207:8081/ai-watch/"
fi

# 创建通知标记文件（供OpenClaw读取）
cat > /tmp/ai-watch-notify.json << EOF
{
    "type": "ai-watch-daily",
    "timestamp": "$(date -Iseconds)",
    "new_count": $NEW_COUNT,
    "message": "$MESSAGE",
    "notified": false
}
EOF

echo "📢 已创建通知标记: /tmp/ai-watch-notify.json"

# 尝试通过飞书Bot API直接发送（需要配置）
# 飞书应用凭证（从OpenClaw配置读取）
FEISHU_APP_ID="cli_a90eefdfae3a9cd4"
FEISHU_APP_SECRET="$(cat /root/.openclaw/openclaw.json 2>/dev/null | grep -o '"appSecret"[^}]*' | cut -d'"' -f4 || echo "")"
USER_ID="ou_84f47f889870e687ec85ad6294317187"

if [ -n "$FEISHU_APP_SECRET" ] && [ "$FEISHU_APP_SECRET" != "" ]; then
    # 获取tenant_access_token
    TOKEN_RESP=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
        -H "Content-Type: application/json" \
        -d "{\"app_id\": \"$FEISHU_APP_ID\", \"app_secret\": \"$FEISHU_APP_SECRET\"}" 2>/dev/null)
    
    TOKEN=$(echo "$TOKEN_RESP" | grep -o '"tenant_access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        # 发送消息
        curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"receive_id\": \"$USER_ID\",
                \"msg_type\": \"text\",
                \"content\": \"{\\\"text\\\": \\\"$MESSAGE\\\"}\"
            }" > /dev/null 2>&1 && echo "✅ 飞书消息已发送" || echo "❌ 飞书消息发送失败"
    else
        echo "⚠️ 无法获取飞书token"
    fi
else
    echo "⚠️ 未配置飞书app_secret，跳过直接发送"
fi

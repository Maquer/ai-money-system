#!/usr/bin/env python3
"""
Discord 销售机器人 - 简化版（无需 discord.py 库）
通过 HTTP Webhook 直接发消息
"""
import requests
import json
import os

# 你的 API 网关
GATEWAY = "http://localhost:8000"

# Webhook URL - 在 Discord 频道设置中创建
# 格式: https://discord.com/api/webhooks/XXX/YYY
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

def send_to_discord(content: str, username: str = "AI Bot"):
    """通过 Webhook 发消息到 Discord"""
    if not WEBHOOK_URL:
        print("⚠️ 未设置 DISCORD_WEBHOOK_URL")
        return False
    try:
        r = requests.post(WEBHOOK_URL, json={
            "username": username,
            "content": content
        })
        return r.status_code == 204
    except Exception as e:
        print(f"❌ Discord 发送失败: {e}")
        return False

def call_ai(prompt: str) -> dict:
    """调用 AI 网关"""
    # 自动注册 + 试用
    user = requests.post(f"{GATEWAY}/v1/register").json()
    requests.post(f"{GATEWAY}/v1/topup/confirm", json={
        "order_id": f"discord_{user['user_id']}",
        "api_key": user['api_key'],
        "amount": 0.1
    })
    # 调用
    r = requests.post(f"{GATEWAY}/v1/chat",
        headers={"Authorization": f"Bearer {user['api_key']}"},
        json={"prompt": prompt},
        timeout=30
    )
    return r.json()

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 测试
    if not WEBHOOK_URL:
        print("=" * 60)
        print("📋 Discord Bot 使用说明")
        print("=" * 60)
        print()
        print("1. 在 Discord 频道中，点击齿轮图标 → Integrations → Webhooks")
        print("2. 创建 Webhook，复制 URL")
        print("3. 设置环境变量:")
        print("   export DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/...'")
        print("4. 运行此脚本")
        print()
        print("💡 也可以用 discord.py 库做完整 Bot（需要 Bot Token）")
    else:
        # 主动推送
        send_to_discord(
            "🤖 **AI Bot 已上线！**\n\n"
            "💡 服务说明:\n"
            "• 每次对话 $0.01\n"
            "• 首次赠送 $0.1 试用\n"
            "• Telegram: @Hermesloong_bot\n"
            "• Web: http://localhost:8000"
        )
        print("✅ 消息已发送到 Discord")

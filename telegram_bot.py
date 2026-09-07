#!/usr/bin/env python3
"""
Telegram 销售机器人 - MVP 版本
功能：用户发送 /key 获取 API Key，发送 /ask 直接提问
"""
import asyncio
import json
import requests
import sys
from datetime import datetime

# 配置
API_GATEWAY = "http://localhost:8000"

# ==================== 简单轮询实现 ====================
class SimpleTelegramBot:
    """使用 HTTP 轮询的简单 Bot（无需额外库）"""

    def __init__(self, token: str):
        self.token = token
        self.api = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.billing_url = f"{API_GATEWAY}/v1"
        self.local_users = {}  # 存储 telegram_user -> api_key

    def get_updates(self):
        """获取新消息"""
        try:
            r = requests.get(f"{self.api}/getUpdates", params={"offset": self.offset, "timeout": 30})
            return r.json().get("result", [])
        except Exception as e:
            print(f"获取更新失败: {e}")
            return []

    def send_message(self, chat_id: int, text: str):
        """发送消息"""
        try:
            requests.post(f"{self.api}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=10)
        except Exception as e:
            print(f"发送失败: {e}")

    def get_or_create_key(self, user_id: int) -> str:
        """获取或创建 API Key"""
        key = f"tg_{user_id}"
        if key in self.local_users:
            return self.local_users[key]

        # 调用 gateway 创建
        r = requests.post(f"{self.billing_url}/register")
        data = r.json()
        self.local_users[key] = data["api_key"]

        # 自动给新用户 $0.1 试用金
        requests.post(f"{self.billing_url}/topup/confirm", json={
            "order_id": f"trial_{user_id}",
            "api_key": data["api_key"],
            "amount": 0.1
        })

        return data["api_key"]

    def get_balance(self, api_key: str) -> float:
        """查询余额"""
        r = requests.get(f"{self.billing_url}/balance",
                        headers={"Authorization": f"Bearer {api_key}"})
        return r.json().get("balance", 0)

    def call_ai(self, api_key: str, prompt: str) -> dict:
        """调用 AI"""
        r = requests.post(f"{self.billing_url}/chat",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt},
            timeout=30
        )
        return r.json()

    def handle_message(self, update: dict):
        """处理消息"""
        message = update.get("message", {})
        if not message:
            return

        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "").strip()

        if not text:
            return

        print(f"[{datetime.now()}] User {user_id}: {text[:50]}")

        # 命令处理
        if text == "/start":
            self.send_message(chat_id,
                "🤖 *AI Bot 欢迎你*\n\n"
                "💡 *命令:*\n"
                "/key - 获取 API Key（送 $0.1 试用）\n"
                "/balance - 查询余额\n"
                "/ask <问题> - 直接提问\n"
                "/buy - 充值\n"
                "/help - 帮助"
            )

        elif text == "/key":
            api_key = self.get_or_create_key(user_id)
            self.send_message(chat_id,
                f"🔑 *你的 API Key:*\n\n"
                f"`{api_key}`\n\n"
                f"💰 已自动赠送 $0.1 试用金\n"
                f"💵 可发起约 10 次对话\n\n"
                f"充值: /buy"
            )

        elif text == "/balance":
            api_key = self.local_users.get(f"tg_{user_id}")
            if not api_key:
                self.send_message(chat_id, "请先 /key 获取 API Key")
                return
            balance = self.get_balance(api_key)
            self.send_message(chat_id, f"💰 余额: `${balance:.4f}`")

        elif text == "/buy":
            self.send_message(chat_id,
                "💳 *充值方式*\n\n"
                "*USDT (TRC20):*\n"
                "`YOUR_USDT_WALLET`\n\n"
                "*档位:*\n"
                "• $5 - 500 次对话\n"
                "• $10 - 1000 次对话\n"
                "• $50 - 5000 次对话\n\n"
                "支付后回复: *paid <金额>*\n"
                "我会自动确认到账"
            )

        elif text.startswith("paid "):
            # 确认支付
            try:
                amount = float(text.replace("paid", "").strip())
                api_key = self.local_users.get(f"tg_{user_id}")
                if api_key:
                    requests.post(f"{self.billing_url}/topup/confirm", json={
                        "order_id": f"manual_{user_id}_{int(datetime.now().timestamp())}",
                        "api_key": api_key,
                        "amount": amount
                    })
                    self.send_message(chat_id, f"✅ 已到账 ${amount}！新余额: ${self.get_balance(api_key):.4f}")
            except:
                self.send_message(chat_id, "格式错误，例: paid 5")

        elif text.startswith("/ask "):
            question = text.replace("/ask", "", 1).strip()
            if not question:
                self.send_message(chat_id, "请输入问题: /ask <你的问题>")
                return

            api_key = self.local_users.get(f"tg_{user_id}")
            if not api_key:
                self.send_message(chat_id, "请先 /key 获取 API Key")
                return

            # 调用 AI
            self.send_message(chat_id, "⏳ 思考中...")
            try:
                result = self.call_ai(api_key, question)
                if "text" in result:
                    self.send_message(chat_id,
                        f"🤖 {result['text'][:3000]}\n\n"
                        f"_💰 余额: ${result.get('balance', 0):.4f}_"
                    )
                else:
                    self.send_message(chat_id, f"❌ 错误: {result}")
            except Exception as e:
                self.send_message(chat_id, f"❌ 请求失败: {e}")

        else:
            # 任何文本都当作问题
            api_key = self.local_users.get(f"tg_{user_id}")
            if api_key and self.get_balance(api_key) > 0:
                try:
                    result = self.call_ai(api_key, text)
                    if "text" in result:
                        self.send_message(chat_id, f"🤖 {result['text'][:3000]}")
                    else:
                        self.send_message(chat_id, f"❌ {result.get('detail', '错误')}")
                except Exception as e:
                    self.send_message(chat_id, f"❌ {e}")
            else:
                self.send_message(chat_id, "请先 /key 获取 API Key（送 $0.1 试用）")

    def run(self):
        """运行 bot"""
        import sys
        print(f"🤖 Bot 启动: {self.api}", flush=True)
        print("等待消息...", flush=True)

        while True:
            updates = self.get_updates()
            for update in updates:
                self.offset = update["update_id"] + 1
                print(f"📩 收到消息: {update.get('message', {}).get('text', '')[:50]}", flush=True)
                self.handle_message(update)
            # 无消息时短暂等待
            if not updates:
                import time
                time.sleep(1)

# ==================== 启动 ====================
if __name__ == "__main__":
    import os

    # 从环境变量获取 Token，或用参数
    token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ 请设置环境变量 TELEGRAM_BOT_TOKEN")
        print("获取方式: 与 @BotFather 对话，发送 /newbot")
        sys.exit(1)

    # 先检查 gateway
    try:
        r = requests.get(f"{API_GATEWAY}/v1/stats", timeout=5)
        print(f"✅ API 网关已连接: {r.json()}")
    except Exception as e:
        print(f"❌ 无法连接 API 网关: {e}")
        print("请先运行: python3 gateway.py")
        sys.exit(1)

    bot = SimpleTelegramBot(token)
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot 停止")

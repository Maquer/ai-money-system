#!/usr/bin/env python3
"""
订阅系统 - SaaS 模式
支持月付/季付/年付，自动续费
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

class SubscriptionManager:
    """订阅管理"""

    PLANS = {
        "free": {
            "name": "免费版",
            "price_monthly": 0,
            "requests_per_day": 20,
            "models": ["basic"],
            "features": ["基础对话"]
        },
        "basic": {
            "name": "基础版",
            "price_monthly": 9.99,
            "requests_per_day": 500,
            "models": ["basic", "standard"],
            "features": ["基础对话", "优先响应", "邮件支持"]
        },
        "pro": {
            "name": "专业版",
            "price_monthly": 29.99,
            "requests_per_day": 5000,
            "models": ["basic", "standard", "premium"],
            "features": ["所有模型", "无限对话", "API 访问", "7×24 支持"]
        },
        "enterprise": {
            "name": "企业版",
            "price_monthly": 99.99,
            "requests_per_day": -1,  # 无限
            "models": ["all"],
            "features": ["所有功能", "专属客服", "SLA 保障", "定制开发"]
        }
    }

    def __init__(self, data_dir: str = "./money_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.subs_file = self.data_dir / "subscriptions.json"
        self.usage_file = self.data_dir / "daily_usage.json"
        self.subs = self._load_subs()
        self.usage = self._load_usage()

    def _load_subs(self) -> dict:
        if self.subs_file.exists():
            with open(self.subs_file) as f:
                return json.load(f)
        return {}

    def _save_subs(self):
        with open(self.subs_file, 'w') as f:
            json.dump(self.subs, f, indent=2)

    def _load_usage(self) -> dict:
        if self.usage_file.exists():
            with open(self.usage_file) as f:
                return json.load(f)
        return {}

    def _save_usage(self):
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage, f, indent=2)

    def subscribe(self, api_key: str, plan: str, duration_months: int = 1) -> dict:
        """订阅"""
        if plan not in self.PLANS:
            return {"error": f"未知套餐: {plan}"}

        plan_info = self.PLANS[plan]
        amount = plan_info["price_monthly"] * duration_months

        now = datetime.now()
        expires = now + timedelta(days=30 * duration_months)

        self.subs[api_key] = {
            "plan": plan,
            "started_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "duration_months": duration_months,
            "amount_paid": amount,
            "auto_renew": False
        }
        self._save_subs()

        return {
            "plan": plan,
            "expires_at": expires.isoformat(),
            "amount": amount,
            "features": plan_info["features"]
        }

    def get_user_plan(self, api_key: str) -> dict:
        """获取用户当前套餐"""
        sub = self.subs.get(api_key)

        if not sub:
            return self.PLANS["free"]

        # 检查是否过期
        expires = datetime.fromisoformat(sub["expires_at"])
        if datetime.now() > expires:
            # 降级到免费
            return self.PLANS["free"]

        return self.PLANS[sub["plan"]]

    def check_quota(self, api_key: str) -> dict:
        """检查配额"""
        plan = self.get_user_plan(api_key)
        today = datetime.now().strftime("%Y-%m-%d")

        # 今日使用量
        user_usage = self.usage.get(api_key, {})
        today_used = user_usage.get(today, 0)

        quota = plan["requests_per_day"]

        if quota == -1:  # 无限
            return {
                "allowed": True,
                "used": today_used,
                "quota": -1,
                "remaining": -1,
                "plan": plan["name"]
            }

        remaining = max(0, quota - today_used)

        return {
            "allowed": remaining > 0,
            "used": today_used,
            "quota": quota,
            "remaining": remaining,
            "plan": plan["name"]
        }

    def record_usage(self, api_key: str):
        """记录使用"""
        today = datetime.now().strftime("%Y-%m-%d")

        if api_key not in self.usage:
            self.usage[api_key] = {}

        self.usage[api_key][today] = self.usage[api_key].get(today, 0) + 1
        self._save_usage()

    def enable_auto_renew(self, api_key: str, enabled: bool = True):
        """开启/关闭自动续费"""
        if api_key in self.subs:
            self.subs[api_key]["auto_renew"] = enabled
            self._save_subs()

    def get_expiring_soon(self, days: int = 3) -> list:
        """获取即将过期的订阅"""
        threshold = datetime.now() + timedelta(days=days)
        expiring = []

        for api_key, sub in self.subs.items():
            expires = datetime.fromisoformat(sub["expires_at"])
            if expires < threshold and expires > datetime.now():
                expiring.append({
                    "api_key": api_key[:12] + "***",
                    "plan": sub["plan"],
                    "expires_at": sub["expires_at"],
                    "auto_renew": sub.get("auto_renew", False)
                })

        return expiring

    def send_renewal_reminders(self, bot_send_func):
        """发送续费提醒"""
        expiring = self.get_expiring_soon(days=3)
        for sub in expiring:
            # 需要关联 telegram user_id
            # 简化：仅返回列表
            print(f"⏰ 提醒: {sub['api_key']} 的 {sub['plan']} 即将过期")


# ==================== 使用示例 ====================
if __name__ == "__main__":
    sm = SubscriptionManager()

    # 模拟用户订阅
    test_key = "sk-test-user"
    result = sm.subscribe(test_key, "pro", 3)
    print(f"订阅结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # 检查配额
    quota = sm.check_quota(test_key)
    print(f"配额: {quota}")

    # 模拟使用
    for _ in range(5):
        sm.record_usage(test_key)
    print(f"使用后: {sm.check_quota(test_key)}")

    # 即将过期
    print(f"即将过期: {sm.get_expiring_soon()}")

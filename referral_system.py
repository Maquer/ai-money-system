#!/usr/bin/env python3
"""
推广系统 - 推荐奖励追踪
推荐人获得 20% 返佣（永久）
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path

class ReferralSystem:
    """推荐奖励系统"""

    COMMISSION_RATE = 0.20  # 20% 返佣

    def __init__(self, data_dir: str = "./money_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.refs_file = self.data_dir / "referrals.json"
        self.refs = self._load()

    def _load(self) -> dict:
        if self.refs_file.exists():
            with open(self.refs_file) as f:
                return json.load(f)
        return {"relations": [], "earnings": {}}

    def _save(self):
        with open(self.refs_file, 'w') as f:
            json.dump(self.refs, f, indent=2)

    def track_referral(self, new_user_id: str, referrer_code: str):
        """记录推荐关系"""
        self.refs["relations"].append({
            "new_user": new_user_id,
            "referrer": referrer_code,
            "timestamp": datetime.now().isoformat(),
            "total_spent": 0,
            "commission_earned": 0
        })
        self._save()

    def record_spending(self, user_id: str, amount: float):
        """记录消费，触发返佣"""
        # 查找推荐人
        referrer = None
        for rel in self.refs["relations"]:
            if rel["new_user"] == user_id:
                referrer = rel["referrer"]
                rel["total_spent"] += amount
                commission = amount * self.COMMISSION_RATE
                rel["commission_earned"] += commission
                break

        if referrer:
            # 累计到推荐人收益
            if referrer not in self.refs["earnings"]:
                self.refs["earnings"][referrer] = {
                    "total_commission": 0,
                    "referral_count": 0,
                    "last_updated": None
                }

            self.refs["earnings"][referrer]["total_commission"] += amount * self.COMMISSION_RATE
            self.refs["earnings"][referrer]["last_updated"] = datetime.now().isoformat()

            # 统计推荐人数
            unique_refs = set(
                r["new_user"] for r in self.refs["relations"]
                if r["referrer"] == referrer
            )
            self.refs["earnings"][referrer]["referral_count"] = len(unique_refs)

            self._save()
            return commission
        return 0

    def get_earnings(self, referrer_code: str) -> dict:
        """获取推荐人收益"""
        return self.refs["earnings"].get(referrer_code, {
            "total_commission": 0,
            "referral_count": 0
        })

    def get_top_referrers(self, n: int = 10) -> list:
        """获取 Top N 推荐人"""
        earnings = self.refs.get("earnings", {})
        sorted_earners = sorted(
            earnings.items(),
            key=lambda x: x[1].get("total_commission", 0),
            reverse=True
        )
        return sorted_earners[:n]

# 测试
if __name__ == "__main__":
    rs = ReferralSystem()

    # 模拟推荐关系
    rs.track_referral("user_001", "promo_MAQUER")
    rs.track_referral("user_002", "promo_MAQUER")
    rs.track_referral("user_003", "promo_OTHER")

    # 模拟消费
    rs.record_spending("user_001", 5.0)  # 推荐人得 $1
    rs.record_spending("user_002", 10.0) # 推荐人得 $2
    rs.record_spending("user_003", 5.0)  # OTHER 得 $1

    # 查看收益
    print("MAQUER 收益:", rs.get_earnings("promo_MAQUER"))
    print("OTHER 收益:", rs.get_earnings("promo_OTHER"))
    print("Top 推荐人:", rs.get_top_referrers())

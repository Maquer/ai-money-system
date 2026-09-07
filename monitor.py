#!/usr/bin/env python3
"""
监控脚本 - 每日检查赚钱系统状态
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("./money_data")
GATEWAY = "http://localhost:8000"

def check_system():
    """检查系统状态"""
    print("=" * 50)
    print(f"📊 系统检查 - {datetime.now()}")
    print("=" * 50)

    # 1. Gateway 健康
    try:
        r = requests.get(f"{GATEWAY}/v1/stats", timeout=5)
        stats = r.json()
        print(f"\n✅ API 网关: 在线")
        print(f"   今日请求: {stats['requests']}")
        print(f"   今日收入: ${stats['revenue']:.4f}")
        print(f"   今日成本: ${stats['cost']:.4f}")
        print(f"   毛利: ${stats['revenue'] - stats['cost']:.4f}")
    except Exception as e:
        print(f"\n❌ API 网关: 离线 ({e})")
        return

    # 2. 用户数
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        with open(users_file) as f:
            users = json.load(f)
        total_balance = sum(u.get("balance", 0) for u in users.values())
        active_users = sum(1 for u in users.values() if u.get("total_requests", 0) > 0)
        print(f"\n👥 用户数据:")
        print(f"   总用户: {len(users)}")
        print(f"   活跃用户: {active_users}")
        print(f"   用户余额合计: ${total_balance:.2f}")

    # 3. 最近 7 天趋势
    usage_file = DATA_DIR / "usage.jsonl"
    if usage_file.exists():
        print(f"\n📈 7 天趋势:")
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_requests = 0
            day_revenue = 0.0
            with open(usage_file) as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec["timestamp"].startswith(day):
                            day_requests += 1
                            day_revenue += rec.get("revenue", 0)
                    except:
                        continue
            bar = "█" * min(day_requests, 50)
            print(f"   {day}: {bar} {day_requests}次 / ${day_revenue:.2f}")

    # 4. 决策建议
    print(f"\n💡 决策建议:")
    if stats['requests'] == 0:
        print("   ⚠️ 今日无请求，需要推广引流")
    elif stats['revenue'] < 0.1:
        print("   ⚠️ 收入偏低，考虑:")
        print("      - 优化定价")
        print("      - 增加免费额度换传播")
        print("      - 接入更多模型")
    elif stats['revenue'] >= 5.0:
        print("   ✅ 达到每日 $5 目标！考虑扩量")
    else:
        print("   📊 继续观察，累积用户")

if __name__ == "__main__":
    check_system()

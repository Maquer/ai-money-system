#!/usr/bin/env python3
"""
USDT 支付监控 - 自动检测链上转账
支持 TRC20 (Tron) 网络
"""
import requests
import time
import json
import hashlib
from datetime import datetime
from pathlib import Path

class USDTMonitor:
    """USDT 支付自动确认"""

    # Tron 网络公共 API（无需 key）
    TRON_API = "https://api.trongrid.io"

    def __init__(self, wallet_address: str, data_dir: str = "./money_data"):
        self.wallet = wallet_address
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.orders_file = self.data_dir / "orders.json"
        self.orders = self._load_orders()

    def _load_orders(self) -> dict:
        """加载订单"""
        if self.orders_file.exists():
            with open(self.orders_file) as f:
                return json.load(f)
        return {}

    def _save_orders(self):
        with open(self.orders_file, 'w') as f:
            json.dump(self.orders, f, indent=2)

    def create_order(self, order_id: str, api_key: str, amount: float) -> dict:
        """创建充值订单"""
        self.orders[order_id] = {
            "api_key": api_key,
            "amount": amount,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "tx_hash": None
        }
        self._save_orders()
        return self.orders[order_id]

    def check_payments(self) -> list:
        """检查所有待支付订单"""
        confirmed = []

        try:
            # 查询最近交易
            response = requests.get(
                f"{self.TRON_API}/v1/accounts/{self.wallet}/transactions/trc20",
                params={"limit": 20, "contract_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"},
                timeout=10
            )

            if response.status_code != 200:
                return confirmed

            data = response.json()
            txs = data.get("data", [])

            for tx in txs:
                # 检查是否是 USDT 转账
                if tx.get("token_info", {}).get("symbol") != "USDT":
                    continue

                # 转入交易
                if tx.get("to") != self.wallet:
                    continue

                # 金额
                amount = float(tx.get("value", 0)) / 1_000_000  # USDT 6位精度

                # 备注（订单号）
                # 实际中需要解析 transaction data
                # 简化：用 tx id 作为标识

                tx_hash = tx.get("transaction_id")
                tx_time = tx.get("block_timestamp", 0)

                # 查找匹配的待支付订单
                for order_id, order in self.orders.items():
                    if order["status"] != "pending":
                        continue
                    if abs(order["amount"] - amount) < 0.01:  # 金额匹配
                        if not order.get("tx_hash"):
                            # 确认
                            self.orders[order_id]["status"] = "confirmed"
                            self.orders[order_id]["tx_hash"] = tx_hash
                            self.orders[order_id]["confirmed_at"] = datetime.now().isoformat()
                            confirmed.append({
                                "order_id": order_id,
                                "amount": amount,
                                "api_key": order["api_key"]
                            })

            self._save_orders()

        except Exception as e:
            print(f"⚠️ USDT 监控错误: {e}")

        return confirmed

    def start_monitoring(self, on_confirmed=None):
        """启动监控循环"""
        print(f"👀 开始监控 USDT 支付: {self.wallet[:8]}...")
        while True:
            try:
                confirmed = self.check_payments()
                for c in confirmed:
                    print(f"✅ 确认支付: {c['order_id']} - ${c['amount']}")
                    if on_confirmed:
                        on_confirmed(c)
            except Exception as e:
                print(f"⚠️ 监控错误: {e}")
            time.sleep(60)  # 每分钟检查一次

# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 替换为你的 USDT 钱包地址
    WALLET = "YOUR_USDT_WALLET_ADDRESS"

    monitor = USDTMonitor(WALLET)

    # 测试：创建订单
    test_order = monitor.create_order(
        order_id="test_001",
        api_key="sk-test",
        amount=5.0
    )
    print(f"订单创建: {json.dumps(test_order, indent=2)}")

    # 检查支付
    confirmed = monitor.check_payments()
    print(f"确认订单: {confirmed}")

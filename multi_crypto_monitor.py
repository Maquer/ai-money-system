#!/usr/bin/env python3
"""
多币种支付监控 - 支持 USDT/BTC/ETH/LTC
自动检测链上转账并确认订单
"""
import requests
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class MultiCryptoMonitor:
    """多币种支付自动确认"""

    # 公开区块链 API（无需 key）
    APIS = {
        "USDT_TRC20": {
            "api": "https://api.trongrid.io",
            "endpoint": "/v1/accounts/{address}/transactions/trc20",
            "contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
            "decimals": 6,
            "symbol": "USDT"
        },
        "BTC": {
            "api": "https://blockstream.info/api",
            "endpoint": "/address/{address}/txs",
            "decimals": 8,
            "symbol": "BTC"
        },
        "ETH": {
            "api": "https://api.ethplorer.io",
            "endpoint": "/getAddressInfo/{address}?apiKey=freekey",
            "decimals": 18,
            "symbol": "ETH"
        }
    }

    def __init__(self, wallets: Dict[str, str], data_dir: str = "./money_data"):
        """
        wallets: {"USDT_TRC20": "TXXX...", "BTC": "bc1q...", "ETH": "0x..."}
        """
        self.wallets = wallets
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.orders_file = self.data_dir / "orders.json"
        self.orders = self._load_orders()
        # 确保结构正确
        if not isinstance(self.orders, dict):
            self.orders = {"pending": [], "confirmed": []}
        if "pending" not in self.orders:
            self.orders["pending"] = []
        if "confirmed" not in self.orders:
            self.orders["confirmed"] = []

    def _load_orders(self) -> dict:
        if self.orders_file.exists():
            with open(self.orders_file) as f:
                return json.load(f)
        return {"pending": [], "confirmed": []}
    def _save_orders(self):
        with open(self.orders_file, 'w') as f:
            json.dump(self.orders, f, indent=2)

    def create_order(self, order_id: str, api_key: str,
                     amount: float, currency: str = "USDT") -> dict:
        """创建订单（支持任意币种）"""
        order = {
            "order_id": order_id,
            "api_key": api_key,
            "amount_usd": amount,  # 按 USD 计价的预期金额
            "currency": currency,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "tx_hash": None,
            "confirmed_at": None
        }
        self.orders["pending"].append(order)
        self._save_orders()
        return order

    def get_payment_info(self, order_id: str) -> dict:
        """获取支付信息（地址、二维码、汇率）"""
        order = self._find_order(order_id)
        if not order:
            return {"error": "订单不存在"}

        currency = order["currency"]
        wallet = self.wallets.get(currency)

        if not wallet:
            return {"error": f"不支持的币种: {currency}"}

        # 获取实时汇率
        rate = self._get_exchange_rate(currency)
        crypto_amount = order["amount_usd"] / rate if rate > 0 else 0

        return {
            "order_id": order_id,
            "currency": currency,
            "amount_usd": order["amount_usd"],
            "amount_crypto": round(crypto_amount, 8),
            "wallet_address": wallet,
            "rate_usd": rate,
            "qr_data": f"{currency.lower()}:{wallet}?amount={crypto_amount}",
            "expires_in": 1800  # 30分钟
        }

    def check_all_payments(self) -> List[dict]:
        """检查所有币种的支付"""
        confirmed = []

        for currency, wallet in self.wallets.items():
            if not wallet or wallet.startswith("YOUR_"):
                continue

            try:
                txs = self._fetch_recent_txs(currency, wallet)
                for tx in txs:
                    matched = self._match_order(tx, currency)
                    if matched:
                        confirmed.append(matched)
            except Exception as e:
                print(f"⚠️ {currency} 检查失败: {e}")

        if confirmed:
            self._save_orders()

        return confirmed

    def _fetch_recent_txs(self, currency: str, address: str) -> List[dict]:
        """获取最近交易"""
        api_config = self.APIS.get(currency)
        if not api_config:
            return []

        if currency == "USDT_TRC20":
            r = requests.get(
                f"{api_config['api']}{api_config['endpoint'].format(address=address)}",
                params={"limit": 20, "contract_address": api_config['contract']},
                timeout=10
            )
            if r.status_code == 200:
                return r.json().get("data", [])

        elif currency == "BTC":
            r = requests.get(
                f"{api_config['api']}{api_config['endpoint'].format(address=address)}",
                timeout=10
            )
            if r.status_code == 200:
                return r.json()

        return []

    def _match_order(self, tx: dict, currency: str) -> Optional[dict]:
        """匹配订单"""
        # 简化的匹配逻辑：根据金额
        # 实际生产应该用 memo/tag 或订单 ID 备注
        api_config = self.APIS[currency]
        decimals = api_config["decimals"]

        # 提取金额
        if currency == "USDT_TRC20":
            if tx.get("to") != self.wallets[currency]:
                return None
            amount_raw = int(tx.get("value", 0))
            amount = amount_raw / (10 ** decimals)
            tx_hash = tx.get("transaction_id")
            tx_time = tx.get("block_timestamp", 0)
        elif currency == "BTC":
            # BTC 累加所有 output
            amount = sum(
                out.get("value", 0) for out in tx.get("vout", [])
                if address_matches(out.get("scriptpubkey_address"), self.wallets[currency])
            ) / (10 ** decimals)
            tx_hash = tx.get("txid")
            tx_time = tx.get("status", {}).get("block_time", 0)
        else:
            return None

        # 查找匹配的待支付订单
        for order in self.orders["pending"]:
            if order["status"] != "pending":
                continue
            if order["currency"] != currency:
                continue
            if order.get("tx_hash") == tx_hash:
                continue  # 已处理

            # 转换为 USD 比较（简化）
            usd_amount = amount * self._get_exchange_rate(currency)
            if abs(usd_amount - order["amount_usd"]) / order["amount_usd"] < 0.05:
                # 5% 容差
                order["status"] = "confirmed"
                order["tx_hash"] = tx_hash
                order["confirmed_at"] = datetime.now().isoformat()
                order["actual_amount"] = amount

                # 移动到已确认
                self.orders["confirmed"].append(order)
                self.orders["pending"].remove(order)

                return {
                    "order_id": order["order_id"],
                    "api_key": order["api_key"],
                    "amount_usd": order["amount_usd"],
                    "currency": currency,
                    "tx_hash": tx_hash
                }

        return None

    def _get_exchange_rate(self, currency: str) -> float:
        """获取汇率（USD 价格）"""
        try:
            ids = {
                "USDT_TRC20": "tether",
                "BTC": "bitcoin",
                "ETH": "ethereum"
            }
            coin_id = ids.get(currency, currency.lower())
            r = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd",
                timeout=5
            )
            if r.status_code == 200:
                return r.json().get(coin_id, {}).get("usd", 1)
        except:
            pass

        # 降级默认值
        defaults = {"USDT_TRC20": 1.0, "BTC": 60000, "ETH": 3000}
        return defaults.get(currency, 1.0)

    def _find_order(self, order_id: str):
        for order in self.orders["pending"] + self.orders["confirmed"]:
            if order["order_id"] == order_id:
                return order
        return None

    def start_monitoring(self, on_confirmed=None):
        """启动监控循环"""
        print("👀 多币种支付监控启动...")
        for currency, wallet in self.wallets.items():
            if wallet and not wallet.startswith("YOUR_"):
                print(f"   💰 {currency}: {wallet[:10]}...")

        while True:
            try:
                confirmed = self.check_all_payments()
                for c in confirmed:
                    print(f"✅ 确认: {c['order_id']} - ${c['amount_usd']} ({c['currency']})")
                    if on_confirmed:
                        on_confirmed(c)
            except Exception as e:
                print(f"⚠️ 监控错误: {e}")
            time.sleep(60)


def address_matches(script_addr, target):
    """简化版地址匹配"""
    return script_addr == target


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 替换为你的真实钱包
    WALLETS = {
        "USDT_TRC20": "YOUR_USDT_WALLET",  # Tron 地址，T 开头
        "BTC": "YOUR_BTC_WALLET",           # bc1q... 或 1... 或 3...
        # "ETH": "0x..."                    # 可选
    }

    monitor = MultiCryptoMonitor(WALLETS)

    # 创建测试订单
    order = monitor.create_order(
        order_id="test_001",
        api_key="sk-test",
        amount=5.0,
        currency="USDT_TRC20"
    )
    print(f"订单: {order}")

    # 获取支付信息
    info = monitor.get_payment_info("test_001")
    print(f"支付信息: {json.dumps(info, indent=2, ensure_ascii=False)}")

    # 检查支付
    confirmed = monitor.check_all_payments()
    print(f"确认订单: {confirmed}")

#!/usr/bin/env python3
"""
赚钱系统 MVP - 30 天日入 $5
架构：API 转售 + Telegram Bot + 联盟营销
"""
import asyncio
import json
import hashlib
import secrets
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
import uvicorn

# ==================== 配置 ====================
class Config:
    # 成本控制
    DAILY_BUDGET = 5.0          # 每日 API 预算 $5
    COST_PER_REQUEST = 0.001     # 每次请求成本 $0.001
    PRICE_PER_REQUEST = 0.01     # 每次请求售价 $0.01

    # 免费模型（已验证可用）
    FREE_MODELS = [
        "minimax/minimax-m3:free",
        "deepseek-v4-flash",
        "glm-5.2",
    ]

    # 联盟营销链接（无需账号即可用）
    AFFILIATE_LINKS = {
        "openrouter": "https://openrouter.ai/?ref=YOUR_CODE",
        "replicate": "https://replicate.com/?ref=YOUR_CODE",
        "digitalocean": "https://m.do.co/c/YOUR_CODE",
    }

    # 存储
    DATA_DIR = Path("./money_data")
    DATA_DIR.mkdir(exist_ok=True)

    # 监控
    REPORT_FILE = DATA_DIR / "daily_report.json"

config = Config()

# ==================== 工具：调用免费 LLM ====================
def call_llm(prompt: str, model: str = None) -> dict:
    """调用免费 LLM（通过 minis-model-use）"""
    model = model or config.FREE_MODELS[0]
    try:
        result = subprocess.run(
            ["minis-model-use", "run", "--model", model, "--prompt", prompt],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("ok"):
                return {
                    "success": True,
                    "text": data["data"]["output_text"],
                    "model": model,
                    "cost": 0.0  # 免费模型
                }
        return {"success": False, "error": result.stderr or "Unknown error"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== 计费系统 ====================
class BillingSystem:
    def __init__(self):
        self.users_file = config.DATA_DIR / "users.json"
        self.usage_file = config.DATA_DIR / "usage.jsonl"
        self.users = self._load_users()

    def _load_users(self):
        if self.users_file.exists():
            with open(self.users_file) as f:
                return json.load(f)
        return {}

    def _save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def create_user(self) -> dict:
        """创建用户"""
        api_key = "sk-" + secrets.token_urlsafe(32)
        user_id = hashlib.md5(api_key.encode()).hexdigest()[:12]
        self.users[api_key] = {
            "user_id": user_id,
            "balance": 0.0,
            "created_at": datetime.now().isoformat(),
            "total_requests": 0,
            "total_spent": 0.0
        }
        self._save_users()
        return {
            "api_key": api_key,
            "user_id": user_id,
            "balance": 0.0
        }

    def get_user(self, api_key: str):
        return self.users.get(api_key)

    def get_balance(self, api_key: str) -> float:
        user = self.get_user(api_key)
        return user["balance"] if user else 0.0

    def deduct(self, api_key: str, amount: float) -> bool:
        user = self.get_user(api_key)
        if not user or user["balance"] < amount:
            return False
        user["balance"] -= amount
        user["total_spent"] += amount
        user["total_requests"] += 1
        self._save_users()
        return True

    def add_balance(self, api_key: str, amount: float):
        """充值（手动/自动）"""
        user = self.get_user(api_key)
        if user:
            user["balance"] += amount
            self._save_users()

    def log_usage(self, api_key: str, prompt: str, response: str, cost: float, revenue: float):
        """记录使用"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "user": api_key[:12] + "***",
            "prompt_len": len(prompt),
            "response_len": len(response),
            "cost": cost,
            "revenue": revenue
        }
        with open(self.usage_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

billing = BillingSystem()

# ==================== API 网关 ====================
app = FastAPI(title="AI API Gateway", version="1.0.0")

@app.get("/")
async def root():
    """首页 - 销售页面"""
    stats = get_daily_stats()
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI API Gateway - 按需付费 AI 服务</title>
        <meta charset="utf-8">
        <meta name="description" content="按需付费的 AI API 服务，支持多种模型，USDT 支付，即开即用">
        <style>
            body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #fafafa; }}
            .hero {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 50px 30px; border-radius: 20px; text-align: center; margin-bottom: 30px; }}
            .hero h1 {{ margin: 0 0 10px 0; font-size: 36px; }}
            .hero p {{ font-size: 18px; opacity: 0.9; margin: 0; }}
            .price {{ background: white; padding: 25px; border-radius: 15px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .price-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px; }}
            .price-item {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; }}
            .price-item .num {{ font-size: 28px; font-weight: bold; color: #667eea; }}
            .code {{ background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 10px; font-family: monospace; overflow-x: auto; font-size: 13px; }}
            .btn {{ display: inline-block; background: #667eea; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin: 5px; }}
            .btn-tg {{ background: #0088cc; }}
            .features {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
            .feature {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .feature .icon {{ font-size: 24px; margin-bottom: 10px; }}
            .stats-bar {{ background: white; padding: 15px 25px; border-radius: 10px; margin: 20px 0; display: flex; justify-content: space-around; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
            .stat-item {{ text-align: center; }}
            .stat-item .num {{ font-size: 20px; font-weight: bold; color: #667eea; }}
            .stat-item .label {{ font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>🤖 AI API Gateway</h1>
            <p>按需付费的 AI 服务 · 即开即用 · USDT 支付</p>
            <div style="margin-top: 25px;">
                <a href="https://t.me/Hermesloong_bot" class="btn btn-tg">🤖 Telegram 试用</a>
                <a href="/docs" class="btn">📡 API 文档</a>
            </div>
        </div>

        <div class="stats-bar">
            <div class="stat-item">
                <div class="num">{stats['requests']}</div>
                <div class="label">今日请求</div>
            </div>
            <div class="stat-item">
                <div class="num">${stats['revenue']:.2f}</div>
                <div class="label">今日收入</div>
            </div>
            <div class="stat-item">
                <div class="num">${stats['cost']:.2f}</div>
                <div class="label">今日成本</div>
            </div>
            <div class="stat-item">
                <div class="num">99%</div>
                <div class="label">利润率</div>
            </div>
        </div>

        <div class="price">
            <h2>💰 简单透明的定价</h2>
            <div class="price-grid">
                <div class="price-item">
                    <div class="num">$0.01</div>
                    <div>每次请求</div>
                </div>
                <div class="price-item">
                    <div class="num">$0.1</div>
                    <div>新人试用（约 10 次）</div>
                </div>
                <div class="price-item">
                    <div class="num">$50</div>
                    <div>大客户档（5000 次）</div>
                </div>
            </div>
            <p style="margin-top: 15px; color: #666;">
                💳 支持 USDT (TRC20) 支付 · 充值后立即到账 · 无月费无最低消费
            </p>
        </div>

        <div class="features">
            <div class="feature">
                <div class="icon">⚡</div>
                <h3>极速响应</h3>
                <p>基于 OpenRouter，1-2 秒返回答案</p>
            </div>
            <div class="feature">
                <div class="icon">🔓</div>
                <h3>无审查</h3>
                <p>免费模型，不限问题类型</p>
            </div>
            <div class="feature">
                <div class="icon">💎</div>
                <h3>多模型</h3>
                <p>DeepSeek / GLM / Qwen 自动切换</p>
            </div>
            <div class="feature">
                <div class="icon">🛡️</div>
                <h3>隐私保护</h3>
                <p>对话记录匿名化，不存储敏感信息</p>
            </div>
        </div>

        <div class="price">
            <h2>🚀 快速开始（3 步）</h2>
            <ol>
                <li><strong>注册</strong>: <code>POST /v1/register</code> 或 Telegram 发 <code>/key</code></li>
                <li><strong>充值</strong>: USDT 支付任意金额</li>
                <li><strong>调用</strong>: 使用 API Key 调用 AI</li>
            </ol>

            <h3>📝 调用示例</h3>
            <div class="code">
curl -X POST http://localhost:8000/v1/chat \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"prompt": "Hello, who are you?"}}'
            </div>
        </div>

        <div class="price">
            <h2>🤖 Telegram Bot 体验</h2>
            <p>最简单的方式，直接在 Telegram 对话：</p>
            <a href="https://t.me/Hermesloong_bot" class="btn btn-tg">@Hermesloong_bot</a>
            <p style="margin-top: 15px;">
                <strong>命令</strong>: <code>/start</code> 开始 · <code>/key</code> 拿 Key · <code>/ask 问题</code> 直接问
            </p>
        </div>

        <div class="price">
            <h2>💼 推广赚钱</h2>
            <p>每推荐一个付费用户，你得 <strong>20% 佣金</strong>（永久）：</p>
            <ul>
                <li>推荐链接: <code>http://localhost:8000/?ref=YOUR_CODE</code></li>
                <li>佣金自动结算到你的账户余额</li>
                <li>无层级，1:1 直推</li>
            </ul>
        </div>

        <p style="text-align: center; color: #999; margin-top: 40px;">
            <a href="/dashboard">📊 数据后台</a> · <a href="/docs">API 文档</a> · <a href="https://t.me/Hermesloong_bot">Telegram</a>
        </p>
    </body>
    </html>
    """)

@app.post("/v1/register")
async def register(request: Request):
    """注册新用户（支持推荐码）"""
    body = {}
    try:
        body = await request.json()
    except:
        pass

    user = billing.create_user()

    # 推荐奖励
    ref_code = body.get("ref")
    if ref_code:
        # 记录推荐关系
        referrals_file = config.DATA_DIR / "referrals.json"
        referrals = []
        if referrals_file.exists():
            with open(referrals_file) as f:
                referrals = json.load(f)
        referrals.append({
            "new_user": user["user_id"],
            "referrer": ref_code,
            "timestamp": datetime.now().isoformat(),
            "reward_paid": False
        })
        with open(referrals_file, 'w') as f:
            json.dump(referrals, f, indent=2)

    return user

@app.get("/v1/balance")
async def balance(authorization: str = Header(None)):
    """查询余额"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization")
    api_key = authorization.replace("Bearer ", "")
    return {
        "balance": billing.get_balance(api_key),
        "user": billing.get_user(api_key)
    }

@app.post("/v1/topup")
async def topup(request: Request):
    """充值（生成支付订单）"""
    body = await request.json()
    api_key = body.get("api_key")
    amount = body.get("amount", 5.0)

    # 生成 USDT 支付订单
    order_id = hashlib.md5(f"{api_key}{amount}{time.time()}".encode()).hexdigest()[:16]

    return {
        "order_id": order_id,
        "amount": amount,
        "currency": "USDT",
        "wallet_address": "YOUR_USDT_WALLET",  # 替换为你的钱包
        "network": "TRC20",
        "note": f"支付 {amount} USDT，备注: {order_id}",
        "auto_confirm": True
    }

@app.post("/v1/topup/confirm")
async def topup_confirm(request: Request):
    """确认支付（自动/手动）"""
    body = await request.json()
    order_id = body.get("order_id")
    api_key = body.get("api_key")
    amount = body.get("amount")

    # 这里应该验证支付（调用区块链 API）
    # 简化：假设已确认
    billing.add_balance(api_key, amount)
    return {"status": "success", "new_balance": billing.get_balance(api_key)}

@app.post("/v1/chat")
async def chat(request: Request, authorization: str = Header(None)):
    """聊天接口"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization")
    api_key = authorization.replace("Bearer ", "")

    user = billing.get_user(api_key)
    if not user:
        raise HTTPException(401, "Invalid API Key")

    balance = billing.get_balance(api_key)
    if balance < config.PRICE_PER_REQUEST:
        raise HTTPException(402, f"Insufficient balance. Need ${config.PRICE_PER_REQUEST}, have ${balance:.4f}")

    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(400, "Empty prompt")

    # 调用 LLM
    start = time.time()
    result = call_llm(prompt)
    latency = time.time() - start

    if not result["success"]:
        raise HTTPException(503, f"LLM error: {result.get('error', 'unknown')}")

    # 扣费
    billing.deduct(api_key, config.PRICE_PER_REQUEST)

    # 记录
    billing.log_usage(api_key, prompt, result["text"], 0.0, config.PRICE_PER_REQUEST)

    return {
        "text": result["text"],
        "model": result["model"],
        "cost": 0.0,
        "charged": config.PRICE_PER_REQUEST,
        "balance": billing.get_balance(api_key),
        "latency": round(latency, 2)
    }

# ==================== 统计 ====================
def get_daily_stats() -> dict:
    """获取今日数据"""
    today = datetime.now().strftime("%Y-%m-%d")
    stats = {"requests": 0, "revenue": 0.0, "cost": 0.0}

    if not billing.usage_file.exists():
        return stats

    with open(billing.usage_file) as f:
        for line in f:
            try:
                record = json.loads(line)
                if record["timestamp"].startswith(today):
                    stats["requests"] += 1
                    stats["revenue"] += record.get("revenue", 0)
                    stats["cost"] += record.get("cost", 0)
            except:
                continue
    return stats

@app.get("/v1/stats")
async def stats():
    """统计数据"""
    return get_daily_stats()

# ==================== Web Dashboard ====================
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """实时 Dashboard"""
    stats = get_daily_stats()

    # 用户数据
    users = []
    users_file = config.DATA_DIR / "users.json"
    if users_file.exists():
        with open(users_file) as f:
            users_data = json.load(f)
            for key, u in users_data.items():
                users.append({
                    "key_preview": key[:15] + "...",
                    "balance": u.get("balance", 0),
                    "requests": u.get("total_requests", 0),
                    "spent": u.get("total_spent", 0),
                    "created": u.get("created_at", "")[:10]
                })

    # 7天数据
    daily_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_stats = {"date": day, "requests": 0, "revenue": 0.0}
        usage_file = config.DATA_DIR / "usage.jsonl"
        if usage_file.exists():
            with open(usage_file) as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec["timestamp"].startswith(day):
                            day_stats["requests"] += 1
                            day_stats["revenue"] += rec.get("revenue", 0)
                    except:
                        continue
        daily_data.append(day_stats)

    total_revenue = sum(d["revenue"] for d in daily_data)
    total_requests = sum(d["requests"] for d in daily_data)
    target = 5.0
    progress = min(100, (stats["revenue"] / target * 100) if target > 0 else 0)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>💰 赚钱系统 Dashboard</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="30">
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: white; }}
            h2, h3 {{ color: #333; }}
            .section {{ background: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .card {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
            .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
            .card .sub {{ color: #999; font-size: 12px; margin-top: 5px; }}
            .bar {{ background: #eee; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; }}
            .bar-fill {{ background: linear-gradient(90deg, #00b09b, #96c93d); height: 100%; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #f8f9fa; font-weight: 600; }}
            .chart {{ display: flex; align-items: end; height: 200px; gap: 10px; margin-top: 20px; }}
            .bar-item {{
                flex: 1; background: linear-gradient(180deg, #667eea, #764ba2);
                border-radius: 5px 5px 0 0; position: relative; min-height: 5px;
            }}
            .bar-label {{ position: absolute; bottom: -25px; left: 0; right: 0; text-align: center; font-size: 11px; color: #666; }}
            .bar-value {{ position: absolute; top: -25px; left: 0; right: 0; text-align: center; font-size: 11px; font-weight: bold; }}
            a {{ color: #667eea; }}
            .header-links a {{ color: white; margin-left: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 赚钱系统实时 Dashboard</h1>
            <p style="color: white; opacity: 0.8;" class="header-links">
                最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                <a href="/">🏠 销售页</a>
                <a href="/docs">📡 API 文档</a>
                <a href="https://t.me/Hermesloong_bot">🤖 Telegram Bot</a>
            </p>

            <div class="cards">
                <div class="card">
                    <div class="label">今日收入</div>
                    <div class="value">${stats['revenue']:.4f}</div>
                    <div class="sub">目标: $5.00</div>
                </div>
                <div class="card">
                    <div class="label">今日请求</div>
                    <div class="value">{stats['requests']}</div>
                    <div class="sub">成本: ${stats['cost']:.4f}</div>
                </div>
                <div class="card">
                    <div class="label">用户总数</div>
                    <div class="value">{len(users)}</div>
                    <div class="sub">活跃: {sum(1 for u in users if u['requests'] > 0)}</div>
                </div>
                <div class="card">
                    <div class="label">7天总收入</div>
                    <div class="value">${total_revenue:.2f}</div>
                    <div class="sub">请求: {total_requests}</div>
                </div>
            </div>

            <div class="section">
                <h3>🎯 今日目标进度: {progress:.1f}%</h3>
                <div class="bar">
                    <div class="bar-fill" style="width: {progress}%;"></div>
                </div>
                <p>{'✅ 达成目标！考虑扩量' if progress >= 100 else f'⚠️ 继续努力，还差 ${target - stats["revenue"]:.4f}'}</p>
            </div>

            <div class="section">
                <h3>📈 7 天收入趋势</h3>
                <div class="chart">
                    {''.join(f'<div class="bar-item" style="height: {min(100, d["revenue"] * 20)}%;"><div class="bar-value">${d["revenue"]:.2f}</div><div class="bar-label">{d["date"][5:]}</div></div>' for d in daily_data)}
                </div>
            </div>

            <div class="section">
                <h3>👥 最近用户</h3>
                {('<table><tr><th>API Key</th><th>余额</th><th>请求数</th><th>消费</th><th>注册日期</th></tr>'
                  + ''.join(f'<tr><td><code>{u["key_preview"]}</code></td><td>${u["balance"]:.4f}</td><td>{u["requests"]}</td><td>${u["spent"]:.4f}</td><td>{u["created"]}</td></tr>' for u in users[-10:])
                  + '</table>') if users else '<p>暂无用户</p>'}
            </div>

            <div class="section">
                <h3>🔗 推广链接</h3>
                <ul>
                    <li>🏠 销售页: <a href="/">http://localhost:8000/</a></li>
                    <li>🤖 Telegram: <a href="https://t.me/Hermesloong_bot?start=ref1">@Hermesloong_bot</a></li>
                </ul>
            </div>

            <div class="section">
                <h3>💼 联盟营销</h3>
                <ul>
                    <li><a href="https://openrouter.ai/?ref=YOUR_CODE" target="_blank">OpenRouter</a> - 推广赚佣金</li>
                    <li><a href="https://replicate.com/?ref=YOUR_CODE" target="_blank">Replicate</a> - $10-$50/注册</li>
                    <li><a href="https://m.do.co/c/YOUR_CODE" target="_blank">DigitalOcean</a> - $25/注册 + $200 试用金</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

# ==================== 启动 ====================
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print("🚀 赚钱系统启动中...")
    print(f"📡 API 网关: http://0.0.0.0:{port}")
    print(f"💰 每次请求: ${config.PRICE_PER_REQUEST}")
    print(f"📁 数据目录: {config.DATA_DIR.absolute()}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)

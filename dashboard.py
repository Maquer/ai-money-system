#!/usr/bin/env python3
"""
Web Dashboard - 实时监控赚钱系统
访问: http://localhost:8000/dashboard
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

GATEWAY_URL = "http://localhost:8000"
DATA_DIR = Path("/var/minis/workspace/money_system/money_data")

dashboard_app = FastAPI()

@dashboard_app.get("/dashboard")
async def dashboard():
    """实时仪表盘"""
    # 获取数据
    try:
        stats = requests.get(f"{GATEWAY_URL}/v1/stats").json()
    except:
        stats = {"requests": 0, "revenue": 0, "cost": 0}

    # 用户数据
    users = []
    users_file = DATA_DIR / "users.json"
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

    # 7 天数据
    daily_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_stats = {"date": day, "requests": 0, "revenue": 0.0}
        usage_file = DATA_DIR / "usage.jsonl"
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

    # 计算汇总
    total_revenue = sum(d["revenue"] for d in daily_data)
    total_requests = sum(d["requests"] for d in daily_data)
    target = 5.0  # 每日目标 $5
    progress = min(100, (stats["revenue"] / target * 100) if target > 0 else 0)

    # 渲染 HTML
    return HTMLResponse(f"""
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
            h1 {{ color: white; margin-bottom: 30px; }}
            .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .card {{
                background: white; padding: 25px; border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
            .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
            .card .sub {{ color: #999; font-size: 12px; margin-top: 5px; }}
            .progress-bar {{
                background: white; padding: 25px; border-radius: 15px; margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .bar {{ background: #eee; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; }}
            .bar-fill {{ background: linear-gradient(90deg, #00b09b, #96c93d); height: 100%; transition: width 0.3s; }}
            .section {{ background: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💰 赚钱系统实时 Dashboard</h1>
            <p style="color: white; opacity: 0.8;">
                最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ·
                <a href="/" style="color: white;">🏠 销售页</a> ·
                <a href="/v1/stats" style="color: white;">📊 API Stats</a>
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

            <div class="progress-bar">
                <h3>🎯 今日目标进度: {progress:.1f}%</h3>
                <div class="bar">
                    <div class="bar-fill" style="width: {progress}%;"></div>
                </div>
                <p style="color: #666; font-size: 14px;">
                    {'✅ 达成目标！考虑扩量' if progress >= 100 else '⚠️ 继续努力，还差 $' + f'{target - stats["revenue"]:.4f}'}
                </p>
            </div>

            <div class="section">
                <h3>📈 7 天收入趋势</h3>
                <div class="chart">
                    {''.join(f'''
                    <div class="bar-item" style="height: {min(100, d['revenue'] * 20)}%;">
                        <div class="bar-value">${d['revenue']:.2f}</div>
                        <div class="bar-label">{d['date'][5:]}</div>
                    </div>
                    ''' for d in daily_data)}
                </div>
            </div>

            <div class="section">
                <h3>👥 用户列表</h3>
                {('<table><tr><th>API Key</th><th>余额</th><th>请求数</th><th>消费</th><th>注册日期</th></tr>'
                  + ''.join(f'<tr><td><code>{u["key_preview"]}</code></td><td>${u["balance"]:.4f}</td><td>{u["requests"]}</td><td>${u["spent"]:.4f}</td><td>{u["created"]}</td></tr>' for u in users[-10:])
                  + '</table>') if users else '<p>暂无用户</p>'}
            </div>

            <div class="section">
                <h3>🔗 推广链接</h3>
                <p>分享这些链接到社交媒体/论坛/群组，每带来一个用户 + $0.1 推荐奖励：</p>
                <ul>
                    <li><a href="{GATEWAY_URL}/?ref=auto">https://api.example.com/?ref=auto</a></li>
                    <li><a href="https://t.me/Hermesloong_bot?start=ref1">Telegram Bot 链接</a></li>
                </ul>
            </div>

            <div class="section">
                <h3>💼 联盟营销</h3>
                <ul>
                    <li><a href="https://openrouter.ai/?ref=YOUR_CODE" target="_blank">OpenRouter</a> - 注册送 $1 佣金</li>
                    <li><a href="https://replicate.com/?ref=YOUR_CODE" target="_blank">Replicate</a> - $10-$50/注册</li>
                    <li><a href="https://m.do.co/c/YOUR_CODE" target="_blank">DigitalOcean</a> - $25/注册 + $200 试用金</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    print("📊 Dashboard 启动: http://localhost:8001/dashboard")
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8001)

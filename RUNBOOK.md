# 赚钱系统运行手册

## 📊 当前状态
- ✅ API 网关已运行在 8000 端口
- ✅ Telegram Bot 代码就绪（需 Bot Token）
- ✅ 监控脚本就绪
- 🎯 目标：30 天日入 $5

## 🚀 快速启动

### 1. 启动 API 网关（如果未运行）
```bash
cd /var/minis/workspace/money_system
python3 gateway.py
```

### 2. 启动 Telegram Bot
```bash
# 1. 与 @BotFather 对话创建 Bot
# 2. 获取 Token
export TELEGRAM_BOT_TOKEN="your_token_here"
python3 telegram_bot.py
```

### 3. 查看数据
```bash
# 实时统计
curl http://localhost:8000/v1/stats

# 详细监控
python3 monitor.py
```

## 💰 收入路径

### 路径 1: API 销售（已实现）
- 用户充值 USDT
- 按 $0.01/次 调用 AI
- 利润率 99%+（上游免费）

### 路径 2: Telegram Bot（已实现）
- 试用金 $0.1（10 次对话）
- 转化付费用户
- 群组推广

### 路径 3: 联盟营销（待启用）
- 嵌入 OpenRouter/Replicate/DO 推广链接
- 每次注册赚 $1-$25

## 📋 30 天计划

| Day | 任务 | 预期 |
|-----|------|------|
| 1-3 | 部署 + 测试 | 系统跑通 |
| 4-7 | 邀请 5 个测试用户 | 验证付费流程 |
| 8-14 | 接入 1-2 个联盟 | 多元化收入 |
| 15-21 | 优化定价/体验 | 提高转化 |
| 22-30 | 扩量推广 | 达到日入 $5 |

## ⚠️ 止损规则

**当以下条件满足时，停止投入：**
- 累计亏损 > $50
- 连续 14 天零收入
- 找不到付费用户

## 📁 文件结构

```
money_system/
├── gateway.py          # API 网关（核心）
├── telegram_bot.py     # Telegram 销售
├── monitor.py          # 监控脚本
├── money_data/         # 数据存储
│   ├── users.json
│   └── usage.jsonl
└── RUNBOOK.md          # 本文档
```

## 🔧 扩展方向

- [ ] 接入 Discord 机器人
- [ ] 创建 Web Dashboard
- [ ] 自动发送使用报告
- [ ] 接入更多免费模型
- [ ] 部署到 VPS（24/7 运行）

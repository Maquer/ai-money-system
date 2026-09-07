# Railway 部署指南

## 🚀 5 分钟部署到 Railway（免费 always-on）

### 步骤 1：注册 Railway
1. 访问 https://railway.app
2. 用 GitHub 账号登录
3. 验证信用卡（不收费，仅验证身份，获得 $5 免费额度）

### 步骤 2：上传代码
**方法 A：GitHub 部署（推荐）**
```bash
# 1. 创建 GitHub 仓库
# 2. 推送代码
cd /var/minis/workspace/money_system
git init
git add .
git commit -m "Money system MVP"
git remote add origin https://github.com/YOUR_USERNAME/money-system.git
git push -u origin main

# 3. 在 Railway 点击 "New Project" → "Deploy from GitHub"
# 4. 选择你的仓库
# 5. Railway 自动检测并部署
```

**方法 B：直接上传**
1. Railway → "New Project" → "Empty Project"
2. 拖拽整个 money_system 文件夹到 Railway

### 步骤 3：配置环境变量
在 Railway 项目设置中添加：
```
TELEGRAM_BOT_TOKEN=你的 Bot Token
PORT=8000
```

### 步骤 4：获得公网 URL
部署成功后，Railway 会给你一个 URL：
```
https://your-app.up.railway.app
```

这就是你的赚钱系统地址！

### 步骤 5：测试
```bash
# 测试销售页
curl https://your-app.up.railway.app/

# 测试 Dashboard
curl https://your-app.up.railway.app/dashboard

# 注册用户
curl -X POST https://your-app.up.railway.app/v1/register
```

---

## 💰 成本
- Railway 免费额度：$5/月
- 预计消耗：约 $1-2/月（小型 FastAPI）
- **相当于免费运行**

## 🔧 部署后配置

### 1. 更新 Telegram Bot Webhook
让 Bot 不再用轮询，改用 Webhook（更稳定）：
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-app.up.railway.app/webhook/telegram"
```

### 2. 启动 Telegram Bot Worker
在 Railway 创建第二个 service，运行：
```bash
TELEGRAM_BOT_TOKEN=<TOKEN> python3 telegram_bot.py
```

### 3. 监控
访问 `https://your-app.up.railway.app/dashboard`

---

## 📋 需要的文件
- ✅ `gateway.py` - API 网关
- ✅ `telegram_bot.py` - Telegram 机器人
- ✅ `requirements.txt` - 依赖
- ✅ `railway.json` - Railway 配置
- ✅ `Procfile` - 启动命令
- ✅ `runtime.txt` - Python 版本

---

## 🆘 故障排除

**问题 1：部署失败**
- 检查 requirements.txt 是否正确
- 查看 Railway 日志

**问题 2：端口错误**
- Railway 自动设置 PORT 环境变量
- 确保代码使用 `os.environ.get("PORT", 8000)`

**问题 3：Bot 收不到消息**
- 确认 TELEGRAM_BOT_TOKEN 设置正确
- 确认 gateway 在运行

---

## 🎯 部署后
- ✅ 真 7×24 运行
- ✅ 公网可访问
- ✅ Telegram Bot 24/7 在线
- ✅ 免费（$5 额度内）

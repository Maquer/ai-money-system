# Railway 自动化部署指南

## ✅ 已完成
- [x] GitHub 仓库创建
- [x] 代码推送
- [x] Railway 配置文件

## 🚀 5 分钟部署步骤

### 1. 注册 Railway
- 访问 https://railway.app
- 用 GitHub 登录（Maquer）
- 添加信用卡（验证身份，**不收费**）
- 获得 $5 免费额度

### 2. 一键部署
**方法 A：从 GitHub 部署**
1. Railway → "New Project"
2. "Deploy from GitHub repo"
3. 选择 `Maquer/ai-money-system`
4. 点击 "Deploy Now"

**方法 B：用 Railway CLI**
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### 3. 配置环境变量
在 Railway 项目页面 → Variables：
```
TELEGRAM_BOT_TOKEN=你的 Bot Token
PORT=8000
```

### 4. 获得公网 URL
部署成功后，Railway 会分配：
```
https://ai-money-system-production.up.railway.app
```

### 5. 部署 Telegram Bot（第二个 service）
1. 在同一项目点 "+ New" → "GitHub Repo"
2. 同样选 `Maquer/ai-money-system`
3. Variables 设置：
   ```
   TELEGRAM_BOT_TOKEN=你的 Bot Token
   ```
4. Settings → Start Command:
   ```
   python3 telegram_bot.py
   ```

### 6. 测试
```bash
# 销售页
curl https://your-app.up.railway.app/

# Dashboard
curl https://your-app.up.railway.app/dashboard

# 注册
curl -X POST https://your-app.up.railway.app/v1/register
```

---

## 💰 成本
- 免费额度：$5/月
- FastAPI 消耗：~ $1-2/月
- **完全够用**

## 🔄 自动部署
- 推送代码到 main → Railway 自动部署
- 不用手动操作

## 🆘 常见问题
**冷启动慢？**
- Railway 一直运行，不会冷启动

**Bot 不响应？**
- 检查 TELEGRAM_BOT_TOKEN 设置
- 查看 Railway Logs

**超出免费额度？**
- 自动暂停，不会扣费
- 充值 $5 可继续

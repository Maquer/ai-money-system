# Vercel 部署指南（5 分钟上线）

## ✅ 为什么选 Vercel？
- 真正 24/7，无休眠
- Serverless 模式，instant response
- 免信用卡
- 免 Dockerfile
- 自动 HTTPS
- 免费额度大（个人项目永远用不完）

## 🚀 部署步骤

### 1. 注册 Vercel
- 访问 https://vercel.com
- 用 GitHub 登录（Maquer）

### 2. 导入项目
1. Vercel → "Add New" → "Project"
2. 选择 `Maquer/ai-money-system`
3. Framework Preset: **Other**
4. 点击 Deploy

### 3. 配置环境变量
项目 → Settings → Environment Variables：
- `TELEGRAM_BOT_TOKEN` = 你的 Bot Token
- `HF_TOKEN` = （可选）

### 4. 获得 URL
部署成功后：
```
https://ai-money-system-maquer.vercel.app
```

### 5. 测试
```bash
# 销售页
curl https://ai-money-system-maquer.vercel.app/

# Dashboard
curl https://ai-money-system-maquer.vercel.app/dashboard

# 注册
curl -X POST https://ai-money-system-maquer.vercel.app/v1/register
```

## 📁 Vercel 部署所需文件（已创建）
- ✅ `vercel.json` - Vercel 配置
- ✅ `api/index.py` - Serverless 入口
- ✅ `requirements.txt` - Python 依赖
- ✅ `gateway.py` - 主应用

## ⚠️ 限制
- 10 秒函数超时（聊天够用）
- 512MB 内存限制
- 数据存储用 `/tmp`（重启会丢，需外接数据库）

## 💡 数据持久化方案
- 升级版：Vercel KV / Postgres（免费额度）
- 简化版：当前用本地文件，重启丢数据可接受（开发期）

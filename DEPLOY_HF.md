# Hugging Face Spaces 部署指南

## ✅ 为什么选 HF Spaces？
- 永久免费
- 7×24 在线（不会冷启动）
- 支持 Docker
- 公网 HTTPS
- 不怕被封

## 🚀 5 分钟部署

### 1. 注册 Hugging Face
- 访问 https://huggingface.co
- 用 GitHub 登录（Maquer）
- 已有账号直接登录

### 2. 创建 Space
1. 访问 https://huggingface.co/new-space
2. 填写：
   - **Space name**: `ai-money-system`
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU basic（免费）
3. 点击 "Create Space"

### 3. 推送代码
Space 创建后，HF 会给你一个 Git 仓库地址：
```
https://huggingface.co/spaces/Maquer/ai-money-system
```

在本地推送：
```bash
cd /var/minis/workspace/money_system
git remote add hf https://USER:TOKEN@huggingface.co/spaces/Maquer/ai-money-system.git
# 创建 HF Token: https://huggingface.co/settings/tokens
git push hf main
```

或者在 HF Space 页面用 Web 上传文件。

### 4. 配置环境变量
在 Space 页面 → Settings → Variables and secrets：
- `TELEGRAM_BOT_TOKEN` = 你的 Bot Token
- `HF_TOKEN` = HF 访问 token（如果需要）

### 5. 等待部署
- HF 自动构建 Docker
- 约 3-5 分钟
- 获得公网 URL：
  ```
  https://Maquer-ai-money-system.hf.space
  ```

### 6. 测试
```bash
# 销售页
curl https://Maquer-ai-money-system.hf.space/

# Dashboard
curl https://Maquer-ai-money-system.hf.space/dashboard

# 注册
curl -X POST https://Maquer-ai-money-system.hf.space/v1/register
```

---

## 💰 成本
- HF Spaces CPU basic: **完全免费**
- 没有时间限制
- 没有休眠

## ⚠️ 限制
- CPU 基础版：2 vCPU, 16GB RAM
- 网络出站有限（但够用）
- 不能跑需要 GPU 的模型

## 🔄 自动部署
- 推送代码到 HF Space 仓库 → 自动部署
- 或用 GitHub Actions 同步

---

## 📊 三个平台对比

| 平台 | 免费 | 7×24 | 难度 |
|------|------|------|------|
| **Hugging Face Spaces** | ✅ 永久 | ✅ | ⭐⭐ 首选 |
| **Render** | ⚠️ 750h/月 | ⚠️ 休眠 | ⭐⭐ 备用 |
| **Fly.io** | ✅ | ✅ | ⭐⭐⭐ 需卡 |

**建议：先用 HF Spaces，如果需要再换。**

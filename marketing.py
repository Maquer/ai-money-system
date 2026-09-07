#!/usr/bin/env python3
"""
营销内容自动生成 - 推广赚钱系统
自动写 Twitter/微博/小红书/公众号推广文案
"""
import json
import subprocess
from datetime import datetime

class MarketingGenerator:
    """营销内容自动生成"""

    PLATFORMS = {
        "twitter": {
            "max_length": 280,
            "style": "简短有力、有 emoji、用 hashtag"
        },
        "weibo": {
            "max_length": 2000,
            "style": "口语化、有热点、@相关账号"
        },
        "xiaohongshu": {
            "max_length": 1000,
            "style": "种草风格、emoji 多、有标题党"
        },
        "wechat_mp": {
            "max_length": 50000,
            "style": "深度长文、有故事、有数据"
        },
        "reddit": {
            "max_length": 40000,
            "style": "技术分享、help 别人、不硬广"
        },
        "v2ex": {
            "max_length": 1000,
            "style": "极客风、技术细节、福利"
        }
    }

    PROMPTS = {
        "launch": """
为{platform}写一条推广文案，主题：AI API Gateway（按需付费 AI 服务）。

要求：
- 风格：{style}
- 字数限制：{max_length}
- 必须包含：1) 痛点 2) 解决方案 3) 价格 4) CTA
- 标签：#AI #API #开发工具
- 不要用：稳赚、保本、第一

输出纯文案，不要解释。
""",
        "tutorial": """
为{platform}写一篇教程，主题：5 分钟用 Python 接入 AI API。

要求：
- 风格：{style}
- 字数：{max_length}
- 结构：痛点 → 代码示例 → 效果展示
- 附完整可运行代码
- CTA：免费试用链接
""",
        "case_study": """
为{platform}写一个用户案例，主题：开发者用 AI API 月省 $200 的故事。

要求：
- 风格：{style}
- 字数：{max_length}
- 有具体数字和场景
- 真实感（不要编造用户名字）
- 结尾有 takeaway
""",
        "comparison": """
为{platform}写一篇对比文章，主题：自建 AI 服务 vs 用 API Gateway。

要求：
- 风格：{style}
- 字数：{max_length}
- 表格对比：成本、稳定性、易用性、扩展性
- 客观中立
- 突出我们优势
"""
    }

    def __init__(self):
        pass

    def generate(self, content_type: str, platform: str) -> dict:
        """生成营销内容"""
        if content_type not in self.PROMPTS:
            return {"error": f"未知类型: {content_type}"}
        if platform not in self.PLATFORMS:
            return {"error": f"不支持的平台: {platform}"}

        platform_info = self.PLATFORMS[platform]
        prompt = self.PROMPTS[content_type].format(
            platform=platform,
            style=platform_info["style"],
            max_length=platform_info["max_length"]
        )

        result = self._call_llm(prompt)
        if result["success"]:
            return {
                "platform": platform,
                "type": content_type,
                "content": result["text"],
                "length": len(result["text"]),
                "generated_at": datetime.now().isoformat()
            }
        return {"error": result.get("error")}

    def generate_calendar(self, days: int = 7) -> list:
        """生成 7 天营销日历"""
        content_types = ["launch", "tutorial", "case_study", "comparison"]
        platforms = ["twitter", "weibo", "xiaohongshu", "v2ex", "reddit"]

        calendar = []
        for day in range(days):
            content_type = content_types[day % len(content_types)]
            platform = platforms[day % len(platforms)]

            item = self.generate(content_type, platform)
            item["day"] = day + 1
            item["publish_date"] = (datetime.now().timestamp() + day * 86400)
            calendar.append(item)

        return calendar

    def _call_llm(self, prompt: str) -> dict:
        """调用 LLM"""
        try:
            result = subprocess.run(
                ["minis-model-use", "run", "--model", "minimax/minimax-m3:free", "--prompt", prompt],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("ok"):
                    return {"success": True, "text": data["data"]["output_text"]}
            return {"success": False, "error": result.stderr or "Unknown"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== 测试 ====================
if __name__ == "__main__":
    mg = MarketingGenerator()

    # 生成单条
    print("=== Twitter 推广 ===")
    result = mg.generate("launch", "twitter")
    if "content" in result:
        print(f"\n{result['content']}\n")
        print(f"字数: {result['length']}/{mg.PLATFORMS['twitter']['max_length']}")
    else:
        print(f"错误: {result}")

    # 生成 7 天日历
    print("\n=== 7 天营销日历 ===")
    calendar = mg.generate_calendar(7)
    for item in calendar:
        if "content" in item:
            print(f"\n📅 Day {item['day']} - {item['platform']} - {item['type']}")
            print(f"   {item['content'][:100]}...")

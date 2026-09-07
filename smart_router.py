#!/usr/bin/env python3
"""
多模型智能路由 - 自动选择最优 LLM
根据：可用性、速度、质量、成本
"""
import subprocess
import json
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

class SmartRouter:
    """智能路由：自动选最快/最便宜的可用模型"""

    # 候选模型（按优先级）
    MODELS = [
        {"id": "minimax/minimax-m3:free", "priority": 1, "type": "free"},
        {"id": "deepseek-v4-flash", "priority": 2, "type": "free"},
        {"id": "glm-5.2", "priority": 3, "type": "free"},
        {"id": "sensenova-6.8-flash-lite", "priority": 4, "type": "free"},
    ]

    # 模型性能历史
    performance_log = {}

    def __init__(self):
        self.health_cache = {}
        self.health_cache_ttl = 300  # 5分钟

    def call(self, prompt: str, prefer: str = "fast") -> Dict:
        """
        调用 LLM
        prefer: "fast" | "quality" | "free"
        """
        # 1. 获取可用模型
        available = self._get_available_models(prefer)

        # 2. 并发尝试（取最快的）
        results = self._race_models(prompt, available)

        # 3. 返回最优
        if results:
            best = min(results, key=lambda x: x.get('latency', 999))
            return best

        return {"success": False, "error": "所有模型都不可用"}

    def _get_available_models(self, prefer: str) -> List[str]:
        """获取可用模型"""
        now = time.time()

        # 过滤掉最近失败的
        available = []
        for model in self.MODELS:
            model_id = model['id']
            last_fail = self.performance_log.get(f"{model_id}_fail", 0)

            if now - last_fail < 60:  # 1分钟内失败过，跳过
                continue

            if prefer == "quality":
                # 优先大模型
                if "ultra" in model_id or "max" in model_id or "pro" in model_id:
                    available.insert(0, model_id)
                else:
                    available.append(model_id)
            else:
                # 默认按优先级
                available.append(model_id)

        return available

    def _race_models(self, prompt: str, models: List[str]) -> List[Dict]:
        """并发调用，取最快返回的"""
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_model = {
                executor.submit(self._call_single, m, prompt): m
                for m in models[:3]  # 最多并发 3 个
            }

            for future in as_completed(future_to_model, timeout=30):
                try:
                    result = future.result()
                    if result['success']:
                        results.append(result)
                        # 一个成功就取消其他（可选）
                        # for f in future_to_model: f.cancel()
                except Exception as e:
                    pass

        return results

    def _call_single(self, model: str, prompt: str) -> Dict:
        """调用单个模型"""
        start = time.time()
        try:
            result = subprocess.run(
                ["minis-model-use", "run", "--model", model, "--prompt", prompt],
                capture_output=True, text=True, timeout=20
            )
            latency = time.time() - start

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("ok"):
                    # 记录成功
                    self.performance_log[f"{model}_ok"] = time.time()
                    return {
                        "success": True,
                        "text": data["data"]["output_text"],
                        "model": model,
                        "latency": latency,
                        "cost": 0.0
                    }

            # 记录失败
            self.performance_log[f"{model}_fail"] = time.time()
            return {"success": False, "model": model, "error": "no_response"}

        except Exception as e:
            self.performance_log[f"{model}_fail"] = time.time()
            return {"success": False, "model": model, "error": str(e)}

# 单例
router = SmartRouter()

# 测试
if __name__ == "__main__":
    print("🧪 测试智能路由...")
    result = router.call("用一句话介绍 Python")
    print(json.dumps(result, ensure_ascii=False, indent=2))

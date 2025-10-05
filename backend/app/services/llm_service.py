"""
LLM Service - 封装大语言模型调用
支持多种LLM提供商（OpenAI, Claude, DeepSeek, SiliconFlow等）
"""
import httpx
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend.app.core.config import settings
from backend.app.models.schemas import Task, TaskType, Priority, UserPreference


class LLMServiceError(Exception):
    """LLM服务相关错误"""
    pass


class LLMService:
    """LLM服务封装类"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.api_key
        self.max_tokens = settings.MAX_TOKENS
        
        # 确保base_url以/v1结尾（用于chat/completions）
        if not self.base_url.endswith('/v1'):
            self.base_url = self.base_url.rstrip('/') + '/v1'
        
        self.chat_url = f"{self.base_url}/chat/completions"
    
    def invoke_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        调用LLM的chat completion接口
        
        Args:
            messages: 对话消息列表，格式 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 温度参数，控制随机性（0-2）
            max_tokens: 最大token数
            
        Returns:
            LLM响应的字典
            
        Raises:
            LLMServiceError: 当调用失败时
        """
        if not self.api_key:
            raise LLMServiceError("API key not configured. Please set OPENAI_API_KEY in .env file")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.chat_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise LLMServiceError("LLM request timeout")
        except httpx.HTTPStatusError as e:
            raise LLMServiceError(f"LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise LLMServiceError(f"LLM service error: {str(e)}")
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """从LLM响应中提取内容"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMServiceError(f"Invalid LLM response structure: {e}")
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应，支持markdown代码块包裹的JSON"""
        content = content.strip()
        
        # 移除可能的markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise LLMServiceError(f"Failed to parse JSON response: {e}\nContent: {content}")
    
    def parse_text_to_task(
        self,
        text: str,
        preference: Optional[UserPreference] = None
    ) -> Dict[str, Any]:
        """
        将自然语言文本解析为结构化任务
        
        Args:
            text: 用户输入的自然语言文本
            preference: 用户偏好设置（可选）
            
        Returns:
            任务字典，包含title, type, estimatedDuration等字段
        """
        system_prompt = self._get_parse_system_prompt()
        user_prompt = self._get_parse_user_prompt(text, preference)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.invoke_chat(messages, temperature=0.2)
        content = self._extract_content(response)
        task_data = self._parse_json_response(content)
        
        # 验证和规范化数据
        return self._normalize_task_data(task_data)
    
    def _get_parse_system_prompt(self) -> str:
        """获取解析任务的系统提示词"""
        return """你是一个专业的日程管理助手。你的任务是将用户的自然语言描述解析为结构化的任务数据。

任务类型说明：
- fixed: 固定任务，有明确的开始和结束时间（如会议、约会）
- flexible: 灵活任务，只有预估时长和可选的截止日期（如写报告、学习）

优先级说明：
- P0: 紧急且重要
- P1: 重要但不紧急
- P2: 不重要但紧急
- P3: 不重要也不紧急

请严格按照以下JSON格式输出，不要包含任何注释或额外文字：

对于固定任务(fixed):
{
  "title": "任务标题",
  "description": "详细描述",
  "type": "fixed",
  "startTime": "2025-10-06T14:00:00",
  "endTime": "2025-10-06T15:00:00",
  "priority": "P1",
  "location": "地点（可选）",
  "tags": ["标签1", "标签2"]
}

对于灵活任务(flexible):
{
  "title": "任务标题",
  "description": "详细描述",
  "type": "flexible",
  "estimatedDuration": 120,
  "deadline": "2025-10-08T18:00:00",
  "priority": "P2",
  "tags": ["标签1", "标签2"]
}

时间格式要求：
- 使用ISO 8601格式：YYYY-MM-DDTHH:MM:SS
- 相对时间转换：
  - "今天" = 当前日期
  - "明天" = 当前日期+1天
  - "后天" = 当前日期+2天
  - "下周X" = 下周对应星期几
  - "上午" = 09:00, "中午" = 12:00, "下午" = 14:00, "晚上" = 19:00

时长单位：
- estimatedDuration使用分钟为单位
- "1小时" = 60, "2小时" = 120, "半小时" = 30

只输出JSON，不要有任何其他文字。"""
    
    def _get_parse_user_prompt(
        self,
        text: str,
        preference: Optional[UserPreference] = None
    ) -> str:
        """获取解析任务的用户提示词"""
        current_time = datetime.now()
        
        prompt = f"""当前时间：{current_time.strftime('%Y-%m-%d %H:%M:%S')}

用户输入：{text}"""
        
        if preference:
            prompt += f"""

用户偏好：
- 最大专注时长：{preference.maxFocusDuration}分钟
- 最小时间块：{preference.minBlockUnit}分钟"""
        
        prompt += """

请将上述自然语言描述解析为JSON格式的任务数据。"""
        
        return prompt
    
    def _normalize_task_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化和验证任务数据"""
        # 确保必要字段存在
        if "title" not in data:
            raise LLMServiceError("Missing required field: title")
        
        if "type" not in data:
            data["type"] = "flexible"
        
        # 验证任务类型
        if data["type"] not in ["fixed", "flexible"]:
            raise LLMServiceError(f"Invalid task type: {data['type']}")
        
        # 验证固定任务的必要字段
        if data["type"] == "fixed":
            if "startTime" not in data or "endTime" not in data:
                raise LLMServiceError("Fixed task must have startTime and endTime")
        
        # 验证灵活任务的必要字段
        if data["type"] == "flexible":
            if "estimatedDuration" not in data:
                # 默认值：2小时
                data["estimatedDuration"] = 120
        
        # 确保优先级有效
        if "priority" not in data:
            data["priority"] = "P2"
        elif data["priority"] not in ["P0", "P1", "P2", "P3"]:
            data["priority"] = "P2"
        
        # 确保tags是列表
        if "tags" not in data:
            data["tags"] = []
        elif not isinstance(data["tags"], list):
            data["tags"] = [str(data["tags"])]
        
        return data


# 全局单例
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取LLM服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# 便捷函数
def parse_text_to_task(text: str, preference: Optional[UserPreference] = None) -> Dict[str, Any]:
    """便捷函数：解析文本为任务"""
    service = get_llm_service()
    return service.parse_text_to_task(text, preference)


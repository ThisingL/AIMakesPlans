"""
Preference Parser - 偏好解析服务
使用LLM将用户的自然语言描述解析为偏好设置
"""
from typing import Dict, Any, Optional

from backend.app.services.llm_service import get_llm_service, LLMServiceError


class PreferenceParser:
    """偏好解析器"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def parse_preference_text(self, text: str) -> Dict[str, Any]:
        """
        将用户描述的工作习惯解析为偏好设置
        
        Args:
            text: 用户的自然语言描述
            
        Returns:
            偏好数据字典
        """
        system_prompt = self._get_preference_system_prompt()
        user_prompt = self._get_preference_user_prompt(text)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm_service.invoke_chat(messages, temperature=0.2)
        content = self.llm_service._extract_content(response)
        pref_data = self.llm_service._parse_json_response(content)
        
        return self._normalize_preference_data(pref_data)
    
    def _get_preference_system_prompt(self) -> str:
        """获取偏好解析的系统提示词"""
        return """你是一个专业的效率管理助手。你的任务是理解用户的工作习惯描述，并转换为结构化的偏好设置。

请根据用户描述，提取以下信息并输出JSON格式：

{
  "workStart": "09:00",           // 工作开始时间（HH:MM格式）
  "workEnd": "18:00",             // 工作结束时间
  "noDisturbSlots": [             // 免打扰时间段列表（可以有多个）
    {"start": "12:00", "end": "13:00", "reason": "午餐"},
    {"start": "18:00", "end": "19:00", "reason": "晚餐"},
    {"start": "22:00", "end": "23:00", "reason": "睡前阅读"}
  ],
  "maxFocusDuration": 120,        // 最大专注时长（分钟）
  "minBlockUnit": 30,             // 最小时间块（分钟）
  "bufferBetweenEvents": 15,      // 事件间缓冲（分钟）
  "preferredFocusTime": "morning" // 偏好专注时间："morning"/"afternoon"/"evening"（可选）
}

提取规则：
1. 工作时间：
   - "早上X点" → workStart
   - "到晚上Y点" → workEnd
   - 如果没说，默认 09:00-18:00

2. 免打扰时间段（可以有多个）：
   - "中午12点到1点午休" → {"start": "12:00", "end": "13:00", "reason": "午餐"}
   - "晚上6点到7点吃晚饭" → {"start": "18:00", "end": "19:00", "reason": "晚餐"}
   - "睡前一小时阅读" → 根据睡觉时间推算，如11点睡，则 {"start": "22:00", "end": "23:00", "reason": "睡前阅读"}
   - 如果有多个，都要列出来
   - 如果没提，返回空数组 []

3. 专注时长：
   - "能连续工作2小时" → maxFocusDuration: 120
   - "每次专注30分钟" → maxFocusDuration: 30
   - "需要每小时休息" → maxFocusDuration: 60
   - 默认：120分钟

4. 最小时间块：
   - "不接受小于30分钟的任务" → minBlockUnit: 30
   - 默认：30分钟

5. 缓冲时间：
   - "任务之间需要15分钟休息" → bufferBetweenEvents: 15
   - 默认：15分钟

6. 偏好时间段：
   - "上午/早上效率高" → "morning"
   - "下午效率好" → "afternoon"
   - "晚上/夜里工作好" → "evening"

只输出JSON，不要其他文字。"""
    
    def _get_preference_user_prompt(self, text: str) -> str:
        """获取用户输入提示"""
        return f"""用户的工作习惯描述：

{text}

请将上述描述解析为偏好设置JSON。"""
    
    def _normalize_preference_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化偏好数据"""
        # 确保必要字段
        if "workStart" not in data:
            data["workStart"] = "09:00"
        if "workEnd" not in data:
            data["workEnd"] = "18:00"
        
        # 构建workingHours
        work_hours = [{
            "start": data["workStart"],
            "end": data["workEnd"]
        }]
        
        # 构建noDisturbSlots（支持多个时间段）
        no_disturb = []
        if "noDisturbSlots" in data and isinstance(data["noDisturbSlots"], list):
            for slot in data["noDisturbSlots"]:
                if "start" in slot and "end" in slot:
                    no_disturb.append({
                        "start": slot["start"],
                        "end": slot["end"]
                    })
        # 兼容旧格式
        elif "lunchStart" in data and "lunchEnd" in data:
            no_disturb.append({
                "start": data["lunchStart"],
                "end": data["lunchEnd"]
            })
        
        # 其他字段使用默认值
        result = {
            "workingHours": work_hours,
            "noDisturbSlots": no_disturb,
            "maxFocusDuration": data.get("maxFocusDuration", 120),
            "minBlockUnit": data.get("minBlockUnit", 30),
            "bufferBetweenEvents": data.get("bufferBetweenEvents", 15)
        }
        
        # 保留额外信息供前端使用
        if "preferredFocusTime" in data:
            result["_preferredFocusTime"] = data["preferredFocusTime"]
        
        return result


# 全局单例
_preference_parser: Optional[PreferenceParser] = None


def get_preference_parser() -> PreferenceParser:
    """获取偏好解析器单例"""
    global _preference_parser
    if _preference_parser is None:
        _preference_parser = PreferenceParser()
    return _preference_parser


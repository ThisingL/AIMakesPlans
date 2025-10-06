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
            # 如果解析失败，可能是LLM返回了多个JSON对象
            # 尝试只取第一个完整的JSON对象
            try:
                # 找到第一个 { 和对应的 }
                start_idx = content.find('{')
                if start_idx == -1:
                    raise LLMServiceError(f"No JSON object found in response: {content}")
                
                # 简单的括号匹配，找到第一个完整的JSON对象
                brace_count = 0
                end_idx = start_idx
                in_string = False
                escape_next = False
                
                for i in range(start_idx, len(content)):
                    char = content[i]
                    
                    if escape_next:
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        continue
                    
                    if not in_string:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                
                first_json = content[start_idx:end_idx]
                return json.loads(first_json)
                
            except Exception as parse_error:
                raise LLMServiceError(f"Failed to parse JSON response: {e}\nContent: {content[:200]}...")
    
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

【重要】任务类型判断规则：

1. **fixed（固定任务）**：用户说了具体的时间点开始做某事
   - "X点有作业/会议/任务" → type: "fixed"（从X点开始）
   - 例子："明天下午4点有作业要写" → type: "fixed", startHour: 16
   - 例子："明天上午10点到11点开会" → type: "fixed", startHour: 10, endHour: 11
   - 例子："下周三下午2点开会" → type: "fixed", startHour: 14
   - 关键词：
     * X点有XXX
     * X点到Y点
     * X点XXX（如"3点开会"）
   - 如果只说了开始时间，没说持续多久：
     * 会议默认1小时
     * 其他任务用estimatedDuration表示
   
2. **flexible（灵活任务）**：只说了时间段或需要多长时间，没有具体时间点
   - "下午做2小时报告" → type: "flexible"（下午某个时候，不是具体几点）
   - "明天做作业，需要半小时" → type: "flexible"
   - 例子："写周报，大概需要1小时" → type: "flexible"
   - 关键词：
     * 做X小时
     * 需要X时间
     * 上午/下午/晚上做XXX（没说具体几点）

优先级说明：
- P0: 紧急且重要（关键词：紧急、必须、立即、马上）
- P1: 重要但不紧急（关键词：重要、关键）
- P2: 普通（默认）
- P3: 不重要也不紧急

严格JSON格式输出规则：

【重要】不要自己计算具体日期！只提取时间关键词，具体日期由系统计算。

1. 固定任务(fixed)格式：

情况A - 明确了开始和结束时间：
{
  "title": "会议",
  "type": "fixed",
  "relativeDate": "下周一",
  "startHour": 10,
  "endHour": 11,
  "startMinute": 0,
  "endMinute": 0,
  "priority": "P1"
}

情况B - 只说了开始时间，给了持续时长：
{
  "title": "写作业",
  "type": "fixed",
  "relativeDate": "明天",
  "startHour": 16,           ← "下午4点"
  "estimatedDuration": 30,   ← "半小时"，系统会自动算出endHour=16.5
  "priority": "P2"
}

注意：
- "下午4点有作业" → startHour: 16, estimatedDuration: 30（如果说了时长）
- "下午4点到5点" → startHour: 16, endHour: 17

2. 灵活任务(flexible)格式：
{
  "title": "写报告",
  "type": "flexible",
  "estimatedDuration": 120,  ← 分钟数
  "relativeDate": "明天",    ← 关键词
  "timePeriod": "下午",      ← 时间段关键词（上午/下午/晚上/全天）
  "priority": "P2"
}

相对日期关键词（直接提取，不计算）：
- 今天、明天、后天、大后天
- 下周一、下周二...下周日
- 本周一、本周二...本周日
- 这个月X号、本月X号（如"这个月19号"）
- X月X号（如"10月19号"）
- X天后（如"3天后"）

时间段关键词：
- "上午"、"下午"、"晚上"、"中午"
- 如果没说时间段 → "全天"

时长提取：
- "1小时" → 60
- "2小时" → 120  
- "半小时" → 30
- "1.5小时" → 90

只输出JSON，不要任何额外文字或markdown标记。"""
    
    def _get_parse_user_prompt(
        self,
        text: str,
        preference: Optional[UserPreference] = None
    ) -> str:
        """获取解析任务的用户提示词"""
        current_time = datetime.now()
        
        # 计算各种相对日期
        tomorrow = current_time + timedelta(days=1)
        day_after = current_time + timedelta(days=2)
        
        # 计算下周的日期（下周一到下周日）
        # 当前是周几（0=周一，6=周日）
        current_weekday = current_time.weekday()
        days_until_next_monday = (7 - current_weekday) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7  # 如果今天是周一，下周一是7天后
        
        next_week_dates = {}
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for i, name in enumerate(weekday_names):
            days_offset = days_until_next_monday + i
            next_date = current_time + timedelta(days=days_offset)
            next_week_dates[name] = next_date.strftime('%Y-%m-%d')
        
        prompt = f"""【当前时间信息】
今天是：{current_time.strftime('%Y年%m月%d日 %A')}
现在时刻：{current_time.strftime('%H:%M:%S')}
明天日期：{tomorrow.strftime('%Y-%m-%d (%A)')}
后天日期：{day_after.strftime('%Y-%m-%d (%A)')}

下周日期参考：
- 下周一：{next_week_dates['周一']}
- 下周二：{next_week_dates['周二']}
- 下周三：{next_week_dates['周三']}
- 下周四：{next_week_dates['周四']}
- 下周五：{next_week_dates['周五']}
- 下周六：{next_week_dates['周六']}
- 下周日：{next_week_dates['周日']}

【用户输入】
{text}"""
        
        if preference:
            prompt += f"""

【用户偏好】
- 最大专注时长：{preference.maxFocusDuration}分钟
- 最小时间块：{preference.minBlockUnit}分钟"""
        
        prompt += """

【任务要求】
请严格按照用户输入的时间要求解析：
- 如果说"明天"，使用明天的日期
- 如果说"今天"，使用今天的日期
- 如果说"下午"，使用14:00作为参考时间
- 如果说"上午"，使用09:00或10:00作为参考时间
- 如果说"X点到Y点"，type必须是"fixed"，必须包含startTime和endTime
- 如果只说"做X小时"，type应该是"flexible"，包含estimatedDuration和deadline

请输出JSON格式的任务数据。"""
        
        return prompt
    
    def _normalize_task_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化和验证任务数据
        使用date_parser将相对日期转换为具体日期
        """
        from backend.app.services.date_parser import parse_relative_date, parse_time_period, build_datetime
        
        # 确保必要字段存在
        if "title" not in data:
            raise LLMServiceError("Missing required field: title")
        
        if "type" not in data:
            data["type"] = "flexible"
        
        # 验证任务类型
        if data["type"] not in ["fixed", "flexible"]:
            raise LLMServiceError(f"Invalid task type: {data['type']}")
        
        current_time = datetime.now()
        
        # 处理固定任务的时间
        if data["type"] == "fixed":
            relative_date = data.get("relativeDate", "今天")
            start_hour = data.get("startHour")
            end_hour = data.get("endHour")
            start_minute = data.get("startMinute", 0)
            end_minute = data.get("endMinute", 0)
            estimated_duration = data.get("estimatedDuration")
            
            if start_hour is None:
                raise LLMServiceError("Fixed task must have startHour")
            
            # 如果没有endHour，但有estimatedDuration，自动计算endHour
            if end_hour is None and estimated_duration:
                # 根据时长计算结束时间
                end_hour = start_hour + (estimated_duration // 60)
                end_minute = start_minute + (estimated_duration % 60)
                # 处理分钟溢出
                if end_minute >= 60:
                    end_hour += 1
                    end_minute -= 60
            elif end_hour is None:
                # 既没有endHour也没有estimatedDuration，默认1小时
                end_hour = start_hour + 1
                end_minute = start_minute
            
            # 使用date_parser精确计算日期
            target_date = parse_relative_date(relative_date, current_time)
            if target_date is None:
                raise LLMServiceError(f"Cannot parse relative date: {relative_date}")
            
            # 构建完整的datetime
            data["startTime"] = build_datetime(target_date, start_hour, start_minute).isoformat()
            data["endTime"] = build_datetime(target_date, end_hour, end_minute).isoformat()
            
            # 移除中间字段
            data.pop("relativeDate", None)
            data.pop("startHour", None)
            data.pop("endHour", None)
            data.pop("startMinute", None)
            data.pop("endMinute", None)
        
        # 处理灵活任务的deadline
        elif data["type"] == "flexible":
            if "estimatedDuration" not in data:
                data["estimatedDuration"] = 120  # 默认2小时
            
            relative_date = data.get("relativeDate", "今天")
            time_period = data.get("timePeriod", "全天")
            
            # 使用date_parser精确计算日期
            target_date = parse_relative_date(relative_date, current_time)
            if target_date is None:
                # 如果无法解析，默认为明天
                target_date = current_time + timedelta(days=1)
            
            # 根据时间段设置deadline
            if time_period == "上午":
                deadline = build_datetime(target_date, 12, 0)
            elif time_period == "下午":
                deadline = build_datetime(target_date, 18, 0)
            elif time_period == "晚上":
                deadline = build_datetime(target_date, 23, 0)
            elif time_period == "中午":
                deadline = build_datetime(target_date, 13, 0)
            else:  # "全天"或其他
                deadline = build_datetime(target_date, 23, 59)
            
            data["deadline"] = deadline.isoformat()
            
            # 移除中间字段
            data.pop("relativeDate", None)
            data.pop("timePeriod", None)
        
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


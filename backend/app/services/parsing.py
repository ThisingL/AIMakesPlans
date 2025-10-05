"""
Parsing Service - 自然语言解析服务
封装解析业务逻辑，调用LLM服务，进行结果验证和后处理
"""
from typing import Optional, Dict, Any
from datetime import datetime

from backend.app.models.schemas import Task, UserPreference, ParseResponse
from backend.app.services.llm_service import get_llm_service, LLMServiceError


class ParsingService:
    """解析服务类"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def parse_text(
        self,
        text: str,
        preference: Optional[UserPreference] = None
    ) -> ParseResponse:
        """
        解析自然语言文本为结构化任务
        
        Args:
            text: 用户输入的自然语言文本
            preference: 用户偏好设置
            
        Returns:
            ParseResponse对象，包含解析后的任务和置信度
            
        Raises:
            ValueError: 当文本为空或解析失败时
            LLMServiceError: 当LLM调用失败时
        """
        # 验证输入
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        text = text.strip()
        
        try:
            # 调用LLM服务解析
            task_data = self.llm_service.parse_text_to_task(text, preference)
            
            # 创建Task对象（会进行Pydantic验证）
            task = Task(**task_data)
            
            # 计算置信度（简单实现，可以后续优化）
            confidence = self._calculate_confidence(text, task_data)
            
            return ParseResponse(
                task=task,
                confidence=confidence
            )
            
        except LLMServiceError as e:
            # LLM调用错误
            raise
        except Exception as e:
            # 其他错误（如数据验证失败）
            raise ValueError(f"Failed to parse text: {str(e)}")
    
    def _calculate_confidence(self, text: str, task_data: Dict[str, Any]) -> float:
        """
        计算解析置信度
        
        这是一个简单的启发式实现，可以根据实际情况优化：
        - 必填字段是否完整
        - 时间信息是否明确
        - 任务描述是否详细
        """
        confidence = 0.7  # 基础分数
        
        # 如果有描述，增加0.1
        if task_data.get("description"):
            confidence += 0.1
        
        # 如果有明确的时间信息，增加0.1
        if task_data.get("type") == "fixed":
            if task_data.get("startTime") and task_data.get("endTime"):
                confidence += 0.1
        elif task_data.get("type") == "flexible":
            if task_data.get("estimatedDuration"):
                confidence += 0.05
            if task_data.get("deadline"):
                confidence += 0.05
        
        # 如果有优先级，增加0.05
        if task_data.get("priority") and task_data["priority"] != "P2":
            confidence += 0.05
        
        # 确保在0-1范围内
        return min(1.0, max(0.0, confidence))


# 全局单例
_parsing_service: Optional[ParsingService] = None


def get_parsing_service() -> ParsingService:
    """获取解析服务单例"""
    global _parsing_service
    if _parsing_service is None:
        _parsing_service = ParsingService()
    return _parsing_service


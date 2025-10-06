"""
Preference Parse API endpoint.
Parse natural language description of work habits into preferences.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any

from backend.app.models.schemas import UserPreference
from backend.app.services.preference_parser import get_preference_parser
from backend.app.services.llm_service import LLMServiceError

router = APIRouter(prefix="/user")


class ParsePreferenceRequest(BaseModel):
    """Request to parse preference from text"""
    text: str = Field(..., min_length=10, max_length=2000, description="用户的工作习惯描述")


class ParsePreferenceResponse(BaseModel):
    """Response with parsed preference"""
    preference: UserPreference
    summary: str = Field(..., description="AI生成的偏好总结")


@router.post("/preferences/parse", response_model=ParsePreferenceResponse)
async def parse_preference(request: ParsePreferenceRequest) -> ParsePreferenceResponse:
    """
    Parse user's work habit description into preference settings.
    
    This endpoint uses AI to understand natural language descriptions of
    work habits and convert them into structured preference settings.
    
    Example input:
    ```
    我是程序员，每天早上9点开始工作，到下午6点。
    我习惯上午做需要思考的工作，下午开会和处理杂事。
    我能连续工作2小时，但需要中间休息15分钟。
    中午12点到1点是午餐时间，不要安排任务。
    ```
    
    Returns:
        Parsed UserPreference and a summary
    """
    try:
        parser = get_preference_parser()
        pref_data = parser.parse_preference_text(request.text)
        
        # 创建UserPreference对象
        preference = UserPreference(**pref_data)
        
        # 生成总结
        summary = _generate_summary(preference, pref_data)
        
        return ParsePreferenceResponse(
            preference=preference,
            summary=summary
        )
        
    except LLMServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI解析失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析错误: {str(e)}"
        )


def _generate_summary(preference: UserPreference, raw_data: Dict[str, Any]) -> str:
    """生成偏好设置的总结"""
    parts = []
    
    # 工作时间
    if preference.workingHours:
        wh = preference.workingHours[0]
        parts.append(f"工作时间：{wh.start} - {wh.end}")
    
    # 午餐时间
    if preference.noDisturbSlots:
        for slot in preference.noDisturbSlots:
            parts.append(f"免打扰：{slot.start} - {slot.end}")
    
    # 专注设置
    parts.append(f"最大专注：{preference.maxFocusDuration}分钟")
    parts.append(f"缓冲时间：{preference.bufferBetweenEvents}分钟")
    
    # 偏好时间
    if "_preferredFocusTime" in raw_data:
        focus_map = {
            "morning": "上午效率最佳",
            "afternoon": "下午效率最佳",
            "evening": "晚上效率最佳"
        }
        parts.append(focus_map.get(raw_data["_preferredFocusTime"], ""))
    
    return "；".join(filter(None, parts)) + "。"


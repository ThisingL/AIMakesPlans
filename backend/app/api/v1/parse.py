"""
Parse API endpoints.
Handles natural language text parsing into structured tasks.
"""
from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import ParseRequest, ParseResponse
from backend.app.services.parsing import get_parsing_service
from backend.app.services.llm_service import LLMServiceError

router = APIRouter(prefix="/parse")


@router.post("", response_model=ParseResponse)
async def parse_text(request: ParseRequest) -> ParseResponse:
    """
    Parse natural language text into a structured task using LLM.
    
    This endpoint uses a Large Language Model to understand natural language
    and convert it into structured task data.
    
    Example inputs:
    - "明天下午做2小时报告"
    - "下周一上午10点到11点开会"
    - "本周五之前完成项目文档"
    
    Returns:
        ParseResponse containing the parsed task and confidence score
    """
    try:
        parsing_service = get_parsing_service()
        result = parsing_service.parse_text(request.text, request.preference)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LLMServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


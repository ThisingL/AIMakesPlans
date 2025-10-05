"""
Integration tests for parsing service with real LLM API.
These tests make actual API calls to the LLM service.

Note: Requires valid API key in .env file.
Skip these tests in CI by using: pytest -m "not integration"
"""
import pytest
from backend.app.services.parsing import get_parsing_service
from backend.app.models.schemas import UserPreference


# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestParsingIntegration:
    """Integration tests with real LLM API"""
    
    def test_parse_flexible_task_chinese(self):
        """Test parsing Chinese text for flexible task"""
        service = get_parsing_service()
        
        result = service.parse_text("明天下午做2小时报告")
        
        assert result.task is not None
        assert result.task.type.value == "flexible"
        assert result.task.estimatedDuration is not None
        assert result.task.title is not None
        assert result.confidence > 0
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"置信度：{result.confidence}")
    
    def test_parse_fixed_task_chinese(self):
        """Test parsing Chinese text for fixed task"""
        service = get_parsing_service()
        
        result = service.parse_text("明天上午10点到11点开会")
        
        assert result.task is not None
        # Should be either fixed or flexible
        assert result.task.type.value in ["fixed", "flexible"]
        assert result.task.title is not None
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"置信度：{result.confidence}")
    
    def test_parse_with_priority(self):
        """Test parsing task with priority keywords"""
        service = get_parsing_service()
        
        result = service.parse_text("紧急：今天必须完成项目文档")
        
        assert result.task is not None
        assert result.task.title is not None
        # Priority should be high (P0 or P1) due to "紧急" keyword
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"优先级：{result.task.priority}")
        print(f"置信度：{result.confidence}")
    
    def test_parse_with_duration(self):
        """Test parsing task with explicit duration"""
        service = get_parsing_service()
        
        result = service.parse_text("写周报，大概需要1小时")
        
        assert result.task is not None
        assert result.task.type.value == "flexible"
        assert result.task.estimatedDuration is not None
        # Duration should be around 60 minutes
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"预估时长：{result.task.estimatedDuration}分钟")
    
    def test_parse_with_deadline(self):
        """Test parsing task with deadline"""
        service = get_parsing_service()
        
        result = service.parse_text("本周五之前完成代码审查")
        
        assert result.task is not None
        assert result.task.type.value == "flexible"
        assert result.task.title is not None
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"截止时间：{result.task.deadline}")
    
    def test_parse_complex_task(self):
        """Test parsing complex task description"""
        service = get_parsing_service()
        
        text = "下周三下午2点在会议室A参加产品评审会议，预计2小时，这是高优先级任务"
        result = service.parse_text(text)
        
        assert result.task is not None
        assert result.task.title is not None
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")
        print(f"任务类型：{result.task.type}")
        print(f"优先级：{result.task.priority}")
    
    def test_parse_with_user_preference(self):
        """Test parsing with user preferences"""
        service = get_parsing_service()
        preference = UserPreference(
            maxFocusDuration=90,
            minBlockUnit=30
        )
        
        result = service.parse_text("学习Python", preference)
        
        assert result.task is not None
        assert result.task.type.value == "flexible"
        
        print(f"\n解析结果：{result.task.model_dump_json(indent=2, exclude_none=True)}")


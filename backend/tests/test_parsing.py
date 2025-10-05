"""
Unit tests for parsing service.
Tests the parsing logic with mocked LLM service.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from backend.app.services.parsing import ParsingService, get_parsing_service
from backend.app.services.llm_service import LLMServiceError
from backend.app.models.schemas import UserPreference, ParseResponse


class TestParsingService:
    """Tests for ParsingService class"""
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_parse_text_success_flexible(self, mock_get_llm):
        """Test successful parsing of flexible task"""
        # Setup mock LLM service
        mock_llm = Mock()
        mock_llm.parse_text_to_task.return_value = {
            "title": "写周报",
            "description": "完成本周工作总结",
            "type": "flexible",
            "estimatedDuration": 60,
            "priority": "P2",
            "tags": ["工作"]
        }
        mock_get_llm.return_value = mock_llm
        
        # Test
        service = ParsingService()
        result = service.parse_text("写周报")
        
        # Verify
        assert isinstance(result, ParseResponse)
        assert result.task.title == "写周报"
        assert result.task.type.value == "flexible"
        assert result.task.estimatedDuration == 60
        assert result.confidence is not None
        assert 0 <= result.confidence <= 1
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_parse_text_success_fixed(self, mock_get_llm):
        """Test successful parsing of fixed task"""
        # Setup mock
        mock_llm = Mock()
        mock_llm.parse_text_to_task.return_value = {
            "title": "团队会议",
            "type": "fixed",
            "startTime": "2025-10-06T10:00:00",
            "endTime": "2025-10-06T11:00:00",
            "priority": "P0"
        }
        mock_get_llm.return_value = mock_llm
        
        # Test
        service = ParsingService()
        result = service.parse_text("明天上午10点开会")
        
        # Verify
        assert result.task.title == "团队会议"
        assert result.task.type.value == "fixed"
        assert result.task.startTime is not None
        assert result.task.endTime is not None
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_parse_text_with_preference(self, mock_get_llm):
        """Test parsing with user preference"""
        # Setup mock
        mock_llm = Mock()
        mock_llm.parse_text_to_task.return_value = {
            "title": "学习",
            "type": "flexible",
            "estimatedDuration": 90,
            "priority": "P1"
        }
        mock_get_llm.return_value = mock_llm
        
        # Test
        preference = UserPreference(maxFocusDuration=90, minBlockUnit=30)
        service = ParsingService()
        result = service.parse_text("学习1.5小时", preference)
        
        # Verify
        mock_llm.parse_text_to_task.assert_called_once()
        call_args = mock_llm.parse_text_to_task.call_args
        assert call_args[0][0] == "学习1.5小时"
        assert call_args[0][1] == preference
    
    def test_parse_text_empty_string(self):
        """Test parsing empty string"""
        service = ParsingService()
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.parse_text("")
    
    def test_parse_text_whitespace_only(self):
        """Test parsing whitespace-only string"""
        service = ParsingService()
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            service.parse_text("   \n\t   ")
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_parse_text_llm_error(self, mock_get_llm):
        """Test handling LLM service error"""
        # Setup mock to raise error
        mock_llm = Mock()
        mock_llm.parse_text_to_task.side_effect = LLMServiceError("API error")
        mock_get_llm.return_value = mock_llm
        
        # Test
        service = ParsingService()
        
        with pytest.raises(LLMServiceError):
            service.parse_text("test text")
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_parse_text_invalid_data(self, mock_get_llm):
        """Test handling invalid task data from LLM"""
        # Setup mock to return invalid data
        mock_llm = Mock()
        mock_llm.parse_text_to_task.return_value = {
            "title": "test",
            "type": "invalid_type"  # Invalid type
        }
        mock_get_llm.return_value = mock_llm
        
        # Test
        service = ParsingService()
        
        with pytest.raises(ValueError):
            service.parse_text("test text")
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_calculate_confidence_with_description(self, mock_get_llm):
        """Test confidence calculation with description"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        service = ParsingService()
        
        # Task with description
        confidence1 = service._calculate_confidence(
            "test",
            {"title": "test", "description": "detailed description", "type": "flexible", "estimatedDuration": 60}
        )
        
        # Task without description
        confidence2 = service._calculate_confidence(
            "test",
            {"title": "test", "type": "flexible", "estimatedDuration": 60}
        )
        
        # Confidence with description should be higher
        assert confidence1 > confidence2
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_calculate_confidence_with_times(self, mock_get_llm):
        """Test confidence calculation with time information"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        service = ParsingService()
        
        # Fixed task with times
        confidence1 = service._calculate_confidence(
            "test",
            {
                "title": "test",
                "type": "fixed",
                "startTime": "2025-10-06T10:00:00",
                "endTime": "2025-10-06T11:00:00"
            }
        )
        
        # Flexible task without deadline
        confidence2 = service._calculate_confidence(
            "test",
            {"title": "test", "type": "flexible", "estimatedDuration": 60}
        )
        
        # Fixed task with times should have higher confidence
        assert confidence1 > confidence2
    
    @patch('backend.app.services.parsing.get_llm_service')
    def test_calculate_confidence_bounds(self, mock_get_llm):
        """Test that confidence is always between 0 and 1"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        service = ParsingService()
        
        # Test various scenarios
        test_data = [
            {"title": "test", "type": "flexible", "estimatedDuration": 60},
            {"title": "test", "description": "desc", "type": "fixed", "startTime": "2025-10-06T10:00:00", "endTime": "2025-10-06T11:00:00", "priority": "P0"},
            {"title": "test"},
        ]
        
        for data in test_data:
            confidence = service._calculate_confidence("test", data)
            assert 0 <= confidence <= 1


class TestParsingServiceHelpers:
    """Tests for helper functions"""
    
    def test_get_parsing_service_singleton(self):
        """Test that get_parsing_service returns singleton"""
        service1 = get_parsing_service()
        service2 = get_parsing_service()
        assert service1 is service2


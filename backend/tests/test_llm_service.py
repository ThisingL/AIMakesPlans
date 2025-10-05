"""
Unit tests for LLM service.
Uses mocking to avoid actual LLM API calls.
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from backend.app.services.llm_service import (
    LLMService,
    LLMServiceError,
    get_llm_service,
    parse_text_to_task
)
from backend.app.models.schemas import UserPreference


class TestLLMService:
    """Tests for LLMService class"""
    
    def test_init(self):
        """Test LLMService initialization"""
        service = LLMService()
        assert service.provider is not None
        assert service.model is not None
        assert service.base_url is not None
        assert service.chat_url.endswith("/chat/completions")
    
    def test_extract_content_success(self):
        """Test extracting content from valid response"""
        service = LLMService()
        response = {
            "choices": [
                {
                    "message": {
                        "content": "test content"
                    }
                }
            ]
        }
        content = service._extract_content(response)
        assert content == "test content"
    
    def test_extract_content_invalid_structure(self):
        """Test extracting content from invalid response"""
        service = LLMService()
        response = {"invalid": "structure"}
        
        with pytest.raises(LLMServiceError):
            service._extract_content(response)
    
    def test_parse_json_response_clean_json(self):
        """Test parsing clean JSON"""
        service = LLMService()
        content = '{"title": "test", "type": "flexible"}'
        result = service._parse_json_response(content)
        assert result["title"] == "test"
        assert result["type"] == "flexible"
    
    def test_parse_json_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        service = LLMService()
        
        # Test ```json ... ```
        content = '```json\n{"title": "test"}\n```'
        result = service._parse_json_response(content)
        assert result["title"] == "test"
        
        # Test ``` ... ```
        content = '```\n{"title": "test"}\n```'
        result = service._parse_json_response(content)
        assert result["title"] == "test"
    
    def test_parse_json_response_invalid_json(self):
        """Test parsing invalid JSON"""
        service = LLMService()
        content = '{invalid json}'
        
        with pytest.raises(LLMServiceError):
            service._parse_json_response(content)
    
    def test_normalize_task_data_valid_flexible(self):
        """Test normalizing valid flexible task data"""
        service = LLMService()
        data = {
            "title": "Test Task",
            "type": "flexible",
            "estimatedDuration": 60,
            "priority": "P1"
        }
        result = service._normalize_task_data(data)
        assert result["title"] == "Test Task"
        assert result["type"] == "flexible"
        assert result["estimatedDuration"] == 60
        assert result["priority"] == "P1"
        assert isinstance(result["tags"], list)
    
    def test_normalize_task_data_valid_fixed(self):
        """Test normalizing valid fixed task data"""
        service = LLMService()
        data = {
            "title": "Meeting",
            "type": "fixed",
            "startTime": "2025-10-06T10:00:00",
            "endTime": "2025-10-06T11:00:00"
        }
        result = service._normalize_task_data(data)
        assert result["title"] == "Meeting"
        assert result["type"] == "fixed"
        assert "priority" in result
        assert isinstance(result["tags"], list)
    
    def test_normalize_task_data_missing_title(self):
        """Test normalizing data with missing title"""
        service = LLMService()
        data = {"type": "flexible"}
        
        with pytest.raises(LLMServiceError):
            service._normalize_task_data(data)
    
    def test_normalize_task_data_invalid_type(self):
        """Test normalizing data with invalid type"""
        service = LLMService()
        data = {"title": "Test", "type": "invalid"}
        
        with pytest.raises(LLMServiceError):
            service._normalize_task_data(data)
    
    def test_normalize_task_data_fixed_missing_times(self):
        """Test normalizing fixed task without times"""
        service = LLMService()
        data = {"title": "Meeting", "type": "fixed"}
        
        with pytest.raises(LLMServiceError):
            service._normalize_task_data(data)
    
    def test_normalize_task_data_defaults(self):
        """Test that defaults are applied correctly"""
        service = LLMService()
        data = {"title": "Test"}
        
        result = service._normalize_task_data(data)
        assert result["type"] == "flexible"
        assert result["priority"] == "P2"
        assert result["tags"] == []
        assert "estimatedDuration" in result


class TestLLMServiceWithMock:
    """Tests for LLMService with mocked HTTP calls"""
    
    @patch('backend.app.services.llm_service.httpx.Client')
    def test_invoke_chat_success(self, mock_client_class):
        """Test successful LLM chat invocation"""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "test response"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Test
        service = LLMService()
        service.api_key = "test-api-key"  # Set a fake API key
        messages = [{"role": "user", "content": "test"}]
        result = service.invoke_chat(messages)
        
        # Verify
        assert "choices" in result
        assert result["choices"][0]["message"]["content"] == "test response"
        mock_client.post.assert_called_once()
    
    @patch('backend.app.services.llm_service.httpx.Client')
    def test_invoke_chat_no_api_key(self, mock_client_class):
        """Test invoke_chat without API key"""
        service = LLMService()
        service.api_key = ""
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(LLMServiceError, match="API key not configured"):
            service.invoke_chat(messages)
    
    @patch('backend.app.services.llm_service.httpx.Client')
    def test_parse_text_to_task_flexible(self, mock_client_class):
        """Test parsing text to flexible task"""
        # Setup mock response
        task_json = {
            "title": "写报告",
            "description": "完成项目报告",
            "type": "flexible",
            "estimatedDuration": 120,
            "priority": "P1",
            "tags": ["工作"]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(task_json, ensure_ascii=False)}}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Test
        service = LLMService()
        result = service.parse_text_to_task("明天下午做2小时报告")
        
        # Verify
        assert result["title"] == "写报告"
        assert result["type"] == "flexible"
        assert result["estimatedDuration"] == 120
        assert result["priority"] == "P1"
    
    @patch('backend.app.services.llm_service.httpx.Client')
    def test_parse_text_to_task_fixed(self, mock_client_class):
        """Test parsing text to fixed task"""
        # Setup mock response
        task_json = {
            "title": "团队会议",
            "type": "fixed",
            "startTime": "2025-10-06T10:00:00",
            "endTime": "2025-10-06T11:00:00",
            "priority": "P0",
            "location": "会议室A"
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(task_json)}}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Test
        service = LLMService()
        result = service.parse_text_to_task("明天上午10点到11点开会")
        
        # Verify
        assert result["title"] == "团队会议"
        assert result["type"] == "fixed"
        assert "startTime" in result
        assert "endTime" in result


class TestLLMServiceHelpers:
    """Tests for helper functions"""
    
    def test_get_llm_service_singleton(self):
        """Test that get_llm_service returns singleton"""
        service1 = get_llm_service()
        service2 = get_llm_service()
        assert service1 is service2
    
    @patch('backend.app.services.llm_service.httpx.Client')
    def test_parse_text_to_task_helper(self, mock_client_class):
        """Test parse_text_to_task helper function"""
        # Setup mock
        task_json = {
            "title": "测试任务",
            "type": "flexible",
            "estimatedDuration": 60
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": json.dumps(task_json, ensure_ascii=False)}}
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post = Mock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        # Test
        result = parse_text_to_task("测试文本")
        
        # Verify
        assert result["title"] == "测试任务"
        assert result["type"] == "flexible"


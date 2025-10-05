"""
Basic LLM API connectivity test.
Simple test to verify AI API is working by asking a basic question.
"""
import pytest
from backend.app.services.llm_service import get_llm_service


@pytest.mark.integration
class TestLLMBasicConnectivity:
    """Basic connectivity tests for LLM API"""
    
    def test_simple_question(self):
        """Test: Ask AI a simple question - '你是谁？'"""
        service = get_llm_service()
        
        messages = [
            {
                "role": "user",
                "content": "你是谁？请简短回答。"
            }
        ]
        
        print("\n" + "="*60)
        print("向AI提问：你是谁？")
        print("="*60)
        
        try:
            response = service.invoke_chat(messages, temperature=0.7)
            
            # 提取AI的回复
            content = service._extract_content(response)
            
            print(f"\nAI回复：\n{content}\n")
            print("="*60)
            
            # 验证
            assert response is not None
            assert "choices" in response
            assert len(content) > 0
            
            print("测试通过！AI API连接正常！")
            
        except Exception as e:
            print(f"\n❌ 测试失败：{e}\n")
            print("="*60)
            raise
    
    def test_simple_math(self):
        """Test: Ask AI a simple math question"""
        service = get_llm_service()
        
        messages = [
            {
                "role": "user", 
                "content": "1+1等于几？只回答数字。"
            }
        ]
        
        print("\n" + "="*60)
        print("向AI提问：1+1等于几？")
        print("="*60)
        
        response = service.invoke_chat(messages, temperature=0.1)
        content = service._extract_content(response)
        
        print(f"\nAI回复：{content}\n")
        print("="*60)
        
        assert response is not None
        assert "2" in content
        
        print("测试通过！AI能正确回答数学问题！")
    
    def test_chinese_understanding(self):
        """Test: Verify AI understands Chinese"""
        service = get_llm_service()
        
        messages = [
            {
                "role": "user",
                "content": "用一句话介绍北京。"
            }
        ]
        
        print("\n" + "="*60)
        print("向AI提问：用一句话介绍北京")
        print("="*60)
        
        response = service.invoke_chat(messages, temperature=0.7)
        content = service._extract_content(response)
        
        print(f"\nAI回复：\n{content}\n")
        print("="*60)
        
        assert response is not None
        assert len(content) > 0
        # 应该包含"北京"或相关词汇
        assert any(word in content for word in ["北京", "首都", "中国"])
        
        print("测试通过！AI能理解和回答中文问题！")
    
    def test_response_format(self):
        """Test: Verify response structure"""
        service = get_llm_service()
        
        messages = [
            {
                "role": "user",
                "content": "说'你好'"
            }
        ]
        
        print("\n" + "="*60)
        print("检查API响应格式")
        print("="*60)
        
        response = service.invoke_chat(messages, temperature=0.7)
        
        print(f"\n响应结构：")
        print(f"- 包含 'choices': {('choices' in response)}")
        print(f"- 包含 'model': {('model' in response)}")
        
        if 'choices' in response and len(response['choices']) > 0:
            choice = response['choices'][0]
            print(f"- choice 包含 'message': {('message' in choice)}")
            if 'message' in choice:
                print(f"- message 包含 'content': {('content' in choice['message'])}")
                print(f"- message 包含 'role': {('role' in choice['message'])}")
        
        print("\n完整响应（JSON）：")
        import json
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("="*60)
        
        # 验证响应格式
        assert "choices" in response
        assert len(response["choices"]) > 0
        assert "message" in response["choices"][0]
        assert "content" in response["choices"][0]["message"]
        
        print("\n测试通过！响应格式正确！")


"""
API演示脚本
展示如何使用后端API的基本功能
"""
import httpx
import json
from datetime import datetime, timedelta


BASE_URL = "http://127.0.0.1:8000"


def print_response(response, title=""):
    """格式化打印API响应"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")


def main():
    """运行API演示"""
    
    print("\n" + "="*60)
    print("  AI Scheduling System - API 演示")
    print("="*60)
    
    with httpx.Client() as client:
        
        # 1. 健康检查
        print("\n1. 健康检查 (GET /health)")
        response = client.get(f"{BASE_URL}/health")
        print_response(response)
        
        # 2. 获取API信息
        print("\n2. 获取API信息 (GET /)")
        response = client.get(f"{BASE_URL}/")
        print_response(response)
        
        # 3. 创建灵活任务
        print("\n3. 创建灵活任务 (POST /v1/tasks)")
        task_data = {
            "task": {
                "title": "写项目文档",
                "description": "完成项目的技术文档编写",
                "type": "flexible",
                "estimatedDuration": 120,
                "priority": "P1",
                "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
                "tags": ["文档", "重要"]
            }
        }
        response = client.post(f"{BASE_URL}/v1/tasks", json=task_data)
        print_response(response)
        
        if response.status_code == 201:
            task1_id = response.json()["id"]
        
        # 4. 创建固定任务
        print("\n4. 创建固定任务 (POST /v1/tasks)")
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        
        fixed_task_data = {
            "task": {
                "title": "团队会议",
                "description": "每周例会",
                "type": "fixed",
                "startTime": start_time.isoformat(),
                "endTime": end_time.isoformat(),
                "priority": "P0",
                "location": "会议室A",
                "tags": ["会议"]
            }
        }
        response = client.post(f"{BASE_URL}/v1/tasks", json=fixed_task_data)
        print_response(response)
        
        if response.status_code == 201:
            task2_id = response.json()["id"]
        
        # 5. 获取所有任务
        print("\n5. 获取所有任务 (GET /v1/tasks)")
        response = client.get(f"{BASE_URL}/v1/tasks")
        print_response(response)
        
        # 6. 获取单个任务
        if 'task1_id' in locals():
            print(f"\n6. 获取单个任务 (GET /v1/tasks/{task1_id})")
            response = client.get(f"{BASE_URL}/v1/tasks/{task1_id}")
            print_response(response)
        
        # 7. 解析自然语言
        print("\n7. 解析自然语言 (POST /v1/parse)")
        parse_data = {
            "text": "明天下午做2小时报告准备",
            "preference": {
                "maxFocusDuration": 120,
                "minBlockUnit": 30
            }
        }
        response = client.post(f"{BASE_URL}/v1/parse", json=parse_data)
        print_response(response)
        
        # 8. 生成调度方案
        print("\n8. 生成调度方案 (POST /v1/schedule/plan)")
        schedule_data = {
            "tasks": [
                {
                    "title": "代码审查",
                    "type": "flexible",
                    "estimatedDuration": 90,
                    "priority": "P1"
                },
                {
                    "title": "写周报",
                    "type": "flexible",
                    "estimatedDuration": 60,
                    "priority": "P2"
                }
            ],
            "existingEvents": [
                {
                    "title": "午餐",
                    "startTime": (datetime.now().replace(hour=12, minute=0)).isoformat(),
                    "endTime": (datetime.now().replace(hour=13, minute=0)).isoformat()
                }
            ],
            "preference": {
                "workingHours": [
                    {"start": "09:00", "end": "18:00"}
                ],
                "maxFocusDuration": 120,
                "bufferBetweenEvents": 15
            },
            "userStatus": {
                "status": "idle",
                "restMode": False
            }
        }
        response = client.post(f"{BASE_URL}/v1/schedule/plan", json=schedule_data)
        print_response(response)
        
        # 9. 删除任务
        if 'task1_id' in locals():
            print(f"\n9. 删除任务 (DELETE /v1/tasks/{task1_id})")
            response = client.delete(f"{BASE_URL}/v1/tasks/{task1_id}")
            print(f"Status Code: {response.status_code}")
            print("任务删除成功！")
    
    print("\n" + "="*60)
    print("  演示完成！")
    print("  访问 http://127.0.0.1:8000/docs 查看完整API文档")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("\n❌ 错误：无法连接到服务器")
        print("请确保服务器正在运行：")
        print("  uvicorn backend.app.main:app --reload")
    except Exception as e:
        print(f"\n❌ 错误：{e}")


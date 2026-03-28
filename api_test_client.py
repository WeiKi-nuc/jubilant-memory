#!/usr/bin/env python3
"""
API 客户端测试脚本
用于演示如何在内网调用智能微习惯追踪器 API
"""
import requests
import json
from datetime import datetime, timedelta

# API 基础地址 - 在内网使用时，将 localhost 替换为运行服务的机器的 IP
# 例如: http://192.168.1.100:8000
BASE_URL = "http://localhost:8000"

def print_response(response, show_data=True):
    """打印响应结果"""
    print(f"状态码: {response.status_code}")
    if show_data:
        try:
            data = response.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(response.text)
    print("-" * 50)

def test_root():
    """测试根路径"""
    print("\n📌 测试: 根路径")
    response = requests.get(f"{BASE_URL}/")
    print_response(response)

def test_get_habits():
    """测试获取所有习惯"""
    print("\n📌 测试: 获取所有习惯")
    response = requests.get(f"{BASE_URL}/api/habits")
    print_response(response)

def test_add_habit(name, frequency="daily"):
    """测试添加习惯"""
    print(f"\n📌 测试: 添加习惯 '{name}'")
    data = {
        "name": name,
        "frequency": frequency
    }
    response = requests.post(f"{BASE_URL}/api/habits", json=data)
    print_response(response)
    if response.status_code == 200:
        return response.json()["habit_id"]
    return None

def test_checkin(habit_id):
    """测试今日打卡"""
    print(f"\n📌 测试: 今日打卡 (习惯ID: {habit_id})")
    response = requests.post(f"{BASE_URL}/api/checkin", params={"habit_id": habit_id})
    print_response(response)

def test_checkin_with_date(habit_id, date_str):
    """测试指定日期打卡"""
    print(f"\n📌 测试: 指定日期打卡 (习惯ID: {habit_id}, 日期: {date_str})")
    data = {
        "habit_id": habit_id,
        "date": date_str
    }
    response = requests.post(f"{BASE_URL}/api/checkin/date", json=data)
    print_response(response)

def test_get_statistics(habit_id):
    """测试获取统计信息"""
    print(f"\n📌 测试: 获取统计信息 (习惯ID: {habit_id})")
    response = requests.get(f"{BASE_URL}/api/habits/{habit_id}/statistics")
    print_response(response)

def test_get_heatmap(habit_id):
    """测试获取热力图"""
    print(f"\n📌 测试: 获取热力图 (习惯ID: {habit_id})")
    response = requests.get(f"{BASE_URL}/api/habits/{habit_id}/heatmap")
    print_response(response)

def test_get_smart_suggestions():
    """测试获取智能建议"""
    print("\n📌 测试: 获取智能建议")
    response = requests.get(f"{BASE_URL}/api/smart-suggestions")
    print_response(response)

def test_delete_habit(habit_id):
    """测试删除习惯"""
    print(f"\n📌 测试: 删除习惯 (习惯ID: {habit_id})")
    response = requests.delete(f"{BASE_URL}/api/habits/{habit_id}")
    print_response(response)

def test_reset_data():
    """测试重置数据"""
    print("\n📌 测试: 重置所有数据")
    response = requests.delete(f"{BASE_URL}/api/data/reset")
    print_response(response)

def test_export_data():
    """测试导出数据"""
    print("\n📌 测试: 导出所有数据")
    response = requests.get(f"{BASE_URL}/api/data/export")
    print_response(response)

def test_run_test_flow():
    """测试运行完整测试流程"""
    print("\n📌 测试: 运行完整测试流程")
    response = requests.post(f"{BASE_URL}/api/test/flow")
    print_response(response)

def demo_complete_workflow():
    """演示完整的用户工作流程"""
    print("=" * 60)
    print("🎬 演示: 完整用户工作流程")
    print("=" * 60)

    # 1. 重置数据
    test_reset_data()

    # 2. 添加两个习惯
    reading_id = test_add_habit("每天阅读30分钟", "daily")
    exercise_id = test_add_habit("每周运动3次", "weekly")

    if not reading_id or not exercise_id:
        print("❌ 添加习惯失败，终止演示")
        return

    # 3. 获取习惯列表
    test_get_habits()

    # 4. 模拟一周打卡
    print("\n📅 模拟一周打卡...")
    today = datetime.now().date()
    
    # 第1-3天: 阅读打卡
    for i in range(6, 3, -1):
        check_date = today - timedelta(days=i)
        test_checkin_with_date(reading_id, check_date.strftime("%Y-%m-%d"))
    
    # 第4天: 忘记打卡 (跳过)
    
    # 第5-7天: 继续阅读打卡
    for i in range(2, -1, -1):
        check_date = today - timedelta(days=i)
        test_checkin_with_date(reading_id, check_date.strftime("%Y-%m-%d"))
    
    # 运动打卡2次
    test_checkin_with_date(exercise_id, (today - timedelta(days=5)).strftime("%Y-%m-%d"))
    test_checkin_with_date(exercise_id, (today - timedelta(days=2)).strftime("%Y-%m-%d"))

    # 5. 今日打卡
    test_checkin(reading_id)

    # 6. 获取统计信息（验证 streak）
    print("\n📊 关键验证: 阅读习惯连续天数应为 3 天（因为中间断了一天）")
    test_get_statistics(reading_id)
    test_get_statistics(exercise_id)

    # 7. 获取热力图
    test_get_heatmap(reading_id)
    test_get_heatmap(exercise_id)

    # 8. 获取智能建议
    test_get_smart_suggestions()

    # 9. 导出数据
    test_export_data()

    # 10. 删除运动习惯
    test_delete_habit(exercise_id)

    # 11. 最终习惯列表
    test_get_habits()

    print("\n" + "=" * 60)
    print("✅ 工作流程演示完成！")
    print("=" * 60)

def show_api_documentation():
    """显示 API 文档信息"""
    print("\n" + "=" * 60)
    print("📚 API 文档地址")
    print("=" * 60)
    print(f"Swagger UI: {BASE_URL}/docs")
    print(f"ReDoc: {BASE_URL}/redoc")
    print("\n💡 在内网访问时，请将 localhost 替换为运行服务的机器的 IP 地址")
    print("   例如: http://192.168.1.100:8000/docs")
    print("=" * 60)

def show_api_endpoints():
    """显示所有可用的 API 端点"""
    print("\n" + "=" * 60)
    print("🔗 可用 API 端点")
    print("=" * 60)
    
    endpoints = [
        ("GET", "/", "根路径，欢迎信息"),
        ("GET", "/api/habits", "获取所有习惯"),
        ("POST", "/api/habits", "添加新习惯"),
        ("DELETE", "/api/habits/{habit_id}", "删除习惯"),
        ("POST", "/api/checkin", "今日打卡"),
        ("POST", "/api/checkin/date", "指定日期打卡（测试用）"),
        ("GET", "/api/habits/{habit_id}/statistics", "获取习惯统计"),
        ("GET", "/api/habits/{habit_id}/heatmap", "获取本周热力图"),
        ("GET", "/api/smart-suggestions", "获取智能建议"),
        ("DELETE", "/api/data/reset", "重置所有数据（测试用）"),
        ("GET", "/api/data/export", "导出所有数据"),
        ("POST", "/api/test/flow", "运行完整测试流程"),
    ]
    
    for method, path, desc in endpoints:
        print(f"{method:6} {path:50} {desc}")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            demo_complete_workflow()
        elif sys.argv[1] == "docs":
            show_api_documentation()
            show_api_endpoints()
        elif sys.argv[1] == "test":
            test_root()
            test_get_habits()
            test_get_smart_suggestions()
        else:
            print("用法:")
            print("  python api_test_client.py demo   # 运行完整工作流演示")
            print("  python api_test_client.py docs   # 显示API文档信息")
            print("  python api_test_client.py test   # 简单测试API连接")
    else:
        show_api_documentation()
        show_api_endpoints()
        print("\n💡 运行示例:")
        print("  python api_test_client.py demo   # 运行完整工作流演示")
        print("  python api_test_client.py docs   # 显示API文档信息")
        print("  python api_test_client.py test   # 简单测试API连接")

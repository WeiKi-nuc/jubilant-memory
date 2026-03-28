"""
API 测试客户端
用于测试 FastAPI 接口
"""
import requests
import json

BASE_URL = "http://localhost:8765"

def test_root():
    """测试根路径"""
    print("=" * 60)
    print("测试 1: 根路径")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_create_habit():
    """测试创建习惯"""
    print("\n" + "=" * 60)
    print("测试 2: 创建习惯")
    print("=" * 60)
    
    # 创建阅读习惯
    resp1 = requests.post(f"{BASE_URL}/api/habits", json={
        "name": "每天阅读30分钟",
        "frequency": "daily"
    })
    print(f"创建阅读 - 状态码: {resp1.status_code}")
    print(f"响应: {json.dumps(resp1.json(), ensure_ascii=False, indent=2)}")
    
    # 创建运动习惯
    resp2 = requests.post(f"{BASE_URL}/api/habits", json={
        "name": "每周运动3次",
        "frequency": "weekly"
    })
    print(f"\n创建运动 - 状态码: {resp2.status_code}")
    print(f"响应: {json.dumps(resp2.json(), ensure_ascii=False, indent=2)}")
    
    return resp1.json(), resp2.json()

def test_list_habits():
    """测试获取习惯列表"""
    print("\n" + "=" * 60)
    print("测试 3: 获取习惯列表")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/api/habits")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_check_in(habit_id):
    """测试打卡"""
    print(f"\n" + "=" * 60)
    print(f"测试 4: 习惯 {habit_id} 打卡")
    print("=" * 60)
    resp = requests.post(f"{BASE_URL}/api/habits/{habit_id}/checkin")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_statistics(habit_id):
    """测试获取统计"""
    print(f"\n" + "=" * 60)
    print(f"测试 5: 习惯 {habit_id} 统计")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/api/habits/{habit_id}/statistics")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_heatmap(habit_id):
    """测试热力图"""
    print(f"\n" + "=" * 60)
    print(f"测试 6: 习惯 {habit_id} 热力图")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/api/habits/{habit_id}/heatmap")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_suggestions():
    """测试智能建议"""
    print("\n" + "=" * 60)
    print("测试 7: 智能建议")
    print("=" * 60)
    resp = requests.get(f"{BASE_URL}/api/suggestions")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def test_simulation():
    """测试模拟功能"""
    print("\n" + "=" * 60)
    print("测试 8: 运行一周模拟")
    print("=" * 60)
    resp = requests.post(f"{BASE_URL}/api/simulation/run", json={
        "days": 7,
        "reading_check_days": [1, 2, 3, 5, 6, 7],  # 第4天不打
        "exercise_check_days": [2, 5]  # 运动2次
    })
    print(f"状态码: {resp.status_code}")
    data = resp.json()
    print(f"响应:")
    print(f"  阅读习惯ID: {data['reading_habit']['id']}")
    print(f"  运动习惯ID: {data['exercise_habit']['id']}")
    print(f"  每日记录:")
    for log in data['daily_logs']:
        print(f"    第{log['day']}天 ({log['date']}): {', '.join(log['actions'])}")
    print(f"  最终统计:")
    print(f"    阅读: {data['final_statistics']['reading']}")
    print(f"    运动: {data['final_statistics']['exercise']}")
    return data

def test_delete_habit(habit_id):
    """测试删除习惯"""
    print(f"\n" + "=" * 60)
    print(f"测试 9: 删除习惯 {habit_id}")
    print("=" * 60)
    resp = requests.delete(f"{BASE_URL}/api/habits/{habit_id}")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")
    return resp.json()

def main():
    print("=" * 60)
    print("习惯追踪器 API 测试客户端")
    print(f"API 地址: {BASE_URL}")
    print("=" * 60)
    
    try:
        # 1. 根路径
        test_root()
        
        # 2. 创建习惯
        reading, exercise = test_create_habit()
        reading_id = reading['id']
        exercise_id = exercise['id']
        
        # 3. 获取列表
        test_list_habits()
        
        # 4. 打卡
        test_check_in(reading_id)
        
        # 5. 统计
        test_statistics(reading_id)
        
        # 6. 热力图
        test_heatmap(reading_id)
        
        # 7. 智能建议
        test_suggestions()
        
        # 8. 运行模拟
        sim_result = test_simulation()
        
        # 9. 删除运动习惯
        test_delete_habit(sim_result['exercise_habit']['id'])
        
        # 10. 查看最终列表
        print("\n" + "=" * 60)
        print("测试 10: 最终习惯列表")
        print("=" * 60)
        final_list = test_list_habits()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print(f"\n错误: 无法连接到 {BASE_URL}")
        print("请确保 API 服务已经启动: python habit_tracker_api.py")
    except Exception as e:
        print(f"\n错误: {e}")

if __name__ == "__main__":
    main()

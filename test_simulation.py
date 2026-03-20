"""
习惯追踪器用户模拟测试脚本
模拟一个真实用户的使用流程
"""

import json
import os
from datetime import datetime, timedelta

# 重置数据文件
def reset_data():
    data = {
        "habits": [],
        "check_ins": {}
    }
    with open("habit_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ 数据已重置")

# 加载数据
def load_data():
    with open("habit_data.json", 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存数据
def save_data(data):
    with open("habit_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 添加习惯
def add_habit(name, frequency):
    data = load_data()
    habit_id = str(len(data["habits"]) + 1)
    habit = {
        "id": habit_id,
        "name": name,
        "frequency": frequency,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["habits"].append(habit)
    save_data(data)
    print(f"✅ 添加习惯: {name} (频率: {frequency}, ID: {habit_id})")
    return habit_id

# 模拟打卡（指定日期）
def check_in_on_date(habit_id, date_str):
    data = load_data()
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    # 检查是否已打卡
    for record in data["check_ins"][habit_id]:
        if record["date"] == date_str:
            print(f"⚠️ 习惯 {habit_id} 在 {date_str} 已经打卡过了")
            return False
    
    record = {
        "date": date_str,
        "timestamp": f"{date_str} 20:00:00"
    }
    data["check_ins"][habit_id].append(record)
    save_data(data)
    print(f"✅ 习惯 {habit_id} 在 {date_str} 打卡成功")
    return True

# 计算连续天数
def calculate_streak(habit_id):
    data = load_data()
    check_ins = data["check_ins"].get(habit_id, [])
    if not check_ins:
        return 0
    
    dates = sorted([record["date"] for record in check_ins], reverse=True)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    if dates[0] not in [today_str, yesterday_str]:
        return 0
    
    streak = 0
    current_date = today if dates[0] == today_str else yesterday
    
    for date_str in dates:
        expected_date = current_date - timedelta(days=streak)
        expected_str = expected_date.strftime("%Y-%m-%d")
        
        if date_str == expected_str:
            streak += 1
        else:
            break
    
    return streak

# 获取统计信息
def get_statistics(habit_id):
    data = load_data()
    check_ins = data["check_ins"].get(habit_id, [])
    
    if not check_ins:
        return {
            "total_check_ins": 0,
            "streak": 0,
            "first_check_in": None,
            "last_check_in": None
        }
    
    dates = sorted([record["date"] for record in check_ins])
    
    return {
        "total_check_ins": len(check_ins),
        "streak": calculate_streak(habit_id),
        "first_check_in": dates[0],
        "last_check_in": dates[-1]
    }

# 删除习惯
def delete_habit(habit_id):
    data = load_data()
    habit = next((h for h in data["habits"] if h["id"] == habit_id), None)
    if habit:
        data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
        if habit_id in data["check_ins"]:
            del data["check_ins"][habit_id]
        save_data(data)
        print(f"✅ 删除习惯 ID {habit_id}: {habit['name']}")
        return True
    print(f"❌ 找不到习惯 ID {habit_id}")
    return False

# 显示所有习惯
def view_habits():
    data = load_data()
    print("\n📚 当前习惯列表:")
    print("-" * 50)
    for habit in data["habits"]:
        stats = get_statistics(habit["id"])
        print(f"  [{habit['id']}] {habit['name']}")
        print(f"      频率: {habit['frequency']} | 总打卡: {stats['total_check_ins']}次 | 连续: {stats['streak']}天")
    print("-" * 50)

# 显示打卡记录
def view_check_ins():
    data = load_data()
    print("\n📝 打卡记录:")
    print("-" * 50)
    for habit_id, records in data["check_ins"].items():
        habit = next((h for h in data["habits"] if h["id"] == habit_id), None)
        name = habit["name"] if habit else "未知"
        dates = [r["date"] for r in records]
        print(f"  {name} (ID: {habit_id}): {dates}")
    print("-" * 50)

def main():
    print("=" * 60)
    print("🧪 习惯追踪器 - 用户模拟测试")
    print("=" * 60)
    
    # 步骤1: 重置数据
    print("\n【步骤1】重置数据文件...")
    reset_data()
    
    # 步骤2: 添加习惯
    print("\n【步骤2】添加两个习惯...")
    reading_id = add_habit("每天阅读30分钟", "daily")
    exercise_id = add_habit("每周运动3次", "weekly")
    
    view_habits()
    
    # 步骤3: 模拟一周使用
    print("\n【步骤3】模拟一周的使用...")
    
    today = datetime.now().date()
    
    # 第1天 (6天前) - 阅读打卡
    day1 = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    print(f"\n📅 第1天 ({day1}):")
    check_in_on_date(reading_id, day1)
    
    # 第2天 (5天前) - 阅读打卡
    day2 = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    print(f"\n📅 第2天 ({day2}):")
    check_in_on_date(reading_id, day2)
    
    # 第3天 (4天前) - 阅读打卡
    day3 = (today - timedelta(days=4)).strftime("%Y-%m-%d")
    print(f"\n📅 第3天 ({day3}):")
    check_in_on_date(reading_id, day3)
    
    # 第4天 (3天前) - 忘记打卡
    day4 = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    print(f"\n📅 第4天 ({day4}):")
    print("😅 用户忘记打卡了...")
    
    # 第5天 (2天前) - 阅读打卡
    day5 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"\n📅 第5天 ({day5}):")
    check_in_on_date(reading_id, day5)
    
    # 第6天 (1天前) - 阅读打卡
    day6 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n📅 第6天 ({day6}):")
    check_in_on_date(reading_id, day6)
    
    # 第7天 (今天) - 阅读打卡
    day7 = today.strftime("%Y-%m-%d")
    print(f"\n📅 第7天 ({day7}):")
    check_in_on_date(reading_id, day7)
    
    # 运动习惯打卡2次
    print("\n🏃 运动习惯打卡:")
    check_in_on_date(exercise_id, day2)  # 第2天
    check_in_on_date(exercise_id, day5)  # 第5天
    
    view_check_ins()
    
    # 步骤4: 查看统计信息
    print("\n【步骤4】查看统计信息...")
    view_habits()
    
    # 验证阅读习惯的streak
    reading_stats = get_statistics(reading_id)
    print(f"\n📊 阅读习惯统计:")
    print(f"   总打卡次数: {reading_stats['total_check_ins']}")
    print(f"   当前连续: {reading_stats['streak']}天")
    print(f"   首次打卡: {reading_stats['first_check_in']}")
    print(f"   最近打卡: {reading_stats['last_check_in']}")
    
    # 验证：streak应该是3天（第5-7天），因为第4天断了
    expected_streak = 3  # 第5、6、7天连续
    if reading_stats['streak'] == expected_streak:
        print(f"\n✅ Streak计算正确！期望: {expected_streak}天, 实际: {reading_stats['streak']}天")
    else:
        print(f"\n❌ Streak计算错误！期望: {expected_streak}天, 实际: {reading_stats['streak']}天")
    
    # 运动习惯统计
    exercise_stats = get_statistics(exercise_id)
    print(f"\n📊 运动习惯统计:")
    print(f"   总打卡次数: {exercise_stats['total_check_ins']}")
    print(f"   当前连续: {exercise_stats['streak']}天")
    print(f"   首次打卡: {exercise_stats['first_check_in']}")
    print(f"   最近打卡: {exercise_stats['last_check_in']}")
    
    # 步骤5: 删除运动习惯
    print("\n【步骤5】删除运动习惯...")
    delete_habit(exercise_id)
    
    # 查看删除后的状态
    print("\n📚 删除后的习惯列表:")
    view_habits()
    
    # 最终数据
    print("\n【最终数据文件内容】")
    data = load_data()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

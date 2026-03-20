from datetime import datetime
from storage import add_habit, delete_habit, get_all_habits, check_in
from logic import calculate_streak, get_weekly_heatmap, get_today_status, get_statistics, calculate_completion_rate
from feedback import get_smart_feedback, predict_tomorrow

def print_header():
    print("\n" + "=" * 50)
    print("🐍 智能微习惯追踪器 (Smart Micro-Habit Tracker)")
    print("=" * 50)

def print_menu():
    print("\n📋 主菜单:")
    print("1. 查看所有习惯")
    print("2. 添加新习惯")
    print("3. 删除习惯")
    print("4. 今日打卡")
    print("5. 查看习惯统计")
    print("6. 查看本周热力图")
    print("7. 获取智能建议")
    print("0. 退出程序")

def view_habits():
    habits = get_all_habits()
    if not habits:
        print("\n📭 还没有任何习惯，快去添加一个吧！")
        return
    
    print("\n📚 我的习惯列表:")
    print("-" * 50)
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        streak = calculate_streak(habit["id"])
        status = "✅" if checked else "⬜"
        print(f"{status} [{habit['id']}] {habit['name']}")
        print(f"    频率: {habit['frequency']} | 连续: {streak}天 | 创建: {habit['created_at'][:10]}")
    print("-" * 50)

def add_new_habit():
    print("\n➕ 添加新习惯")
    name = input("请输入习惯名称: ").strip()
    if not name:
        print("❌ 习惯名称不能为空！")
        return
    
    print("\n选择频率:")
    print("1. 每天 (daily)")
    print("2. 每周 (weekly)")
    freq_choice = input("请选择 (1/2): ").strip()
    frequency = "daily" if freq_choice != "2" else "weekly"
    
    success, habit_id = add_habit(name, frequency)
    if success:
        print(f"✅ 习惯添加成功！ID: {habit_id}")
    else:
        print("❌ 添加失败，请重试！")

def delete_habit_menu():
    view_habits()
    habit_id = input("\n请输入要删除的习惯ID: ").strip()
    if not habit_id:
        print("❌ 无效的ID！")
        return
    
    confirm = input(f"确认删除习惯 {habit_id}？(y/n): ").lower()
    if confirm == 'y':
        if delete_habit(habit_id):
            print("✅ 删除成功！")
        else:
            print("❌ 删除失败！")
    else:
        print("已取消删除。")

def check_in_today():
    habits = get_all_habits()
    if not habits:
        print("\n📭 还没有任何习惯，快去添加一个吧！")
        return
    
    print("\n✨ 今日打卡")
    print("-" * 50)
    for habit in habits:
        checked, timestamp = get_today_status(habit["id"])
        streak = calculate_streak(habit["id"])
        status = "✅" if checked else "⬜"
        print(f"{status} [{habit['id']}] {habit['name']} (连续{streak}天)")
    print("-" * 50)
    
    habit_id = input("\n请输入要打卡的习惯ID: ").strip()
    if not habit_id:
        print("❌ 无效的ID！")
        return
    
    success, message = check_in(habit_id)
    if success:
        streak = calculate_streak(habit_id)
        completion_rate = calculate_completion_rate(habit_id)
        print(f"\n{message}")
        print(get_smart_feedback(streak, completion_rate))
    else:
        print(f"\n⚠️ {message}")

def view_statistics():
    habits = get_all_habits()
    if not habits:
        print("\n📭 还没有任何习惯，快去添加一个吧！")
        return
    
    view_habits()
    habit_id = input("\n请输入要查看的习惯ID: ").strip()
    if not habit_id:
        print("❌ 无效的ID！")
        return
    
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        print("❌ 找不到该习惯！")
        return
    
    stats = get_statistics(habit_id)
    
    print(f"\n📊 习惯统计: {habit['name']}")
    print("=" * 50)
    print(f"总打卡次数: {stats['total_check_ins']}次")
    print(f"当前连续: {stats['streak']}天")
    print(f"近7天完成率: {stats['completion_rate_7d']*100:.1f}%")
    print(f"首次打卡: {stats['first_check_in'] or '未打卡'}")
    print(f"最近打卡: {stats['last_check_in'] or '未打卡'}")
    print("=" * 50)

def view_heatmap():
    habits = get_all_habits()
    if not habits:
        print("\n📭 还没有任何习惯，快去添加一个吧！")
        return
    
    view_habits()
    habit_id = input("\n请输入要查看的习惯ID: ").strip()
    if not habit_id:
        print("❌ 无效的ID！")
        return
    
    heatmap = get_weekly_heatmap(habit_id)
    
    print("\n📅 本周打卡热力图:")
    print("=" * 50)
    
    for day in heatmap:
        status = "🟩" if day["checked"] else "⬜"
        print(f"{status} {day['day']} ({day['date']})")
    
    print("=" * 50)
    
    checked_count = sum(1 for d in heatmap if d["checked"])
    print(f"本周完成: {checked_count}/7 天")

def get_smart_suggestion():
    habits = get_all_habits()
    if not habits:
        print("\n📭 还没有任何习惯，快去添加一个吧！")
        return
    
    print("\n🔮 智能建议")
    print("=" * 50)
    
    unchecked = []
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        if not checked:
            unchecked.append(habit)
    
    if unchecked:
        print("今天还没打卡的习惯:")
        for h in unchecked:
            streak = calculate_streak(h["id"])
            print(f"  ⬜ {h['name']} (连续{streak}天)")
        print()
    else:
        print("🎉 太棒了！今天所有习惯都已完成！\n")
    
    print(f"🔮 {predict_tomorrow()}")
    print("=" * 50)

def main():
    print_header()
    
    while True:
        print_menu()
        choice = input("\n请选择操作: ").strip()
        
        if choice == '1':
            view_habits()
        elif choice == '2':
            add_new_habit()
        elif choice == '3':
            delete_habit_menu()
        elif choice == '4':
            check_in_today()
        elif choice == '5':
            view_statistics()
        elif choice == '6':
            view_heatmap()
        elif choice == '7':
            get_smart_suggestion()
        elif choice == '0':
            print("\n👋 感谢使用智能微习惯追踪器，再见！")
            break
        else:
            print("❌ 无效的选择，请重试！")

if __name__ == "__main__":
    main()

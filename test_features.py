"""
测试热力图和智能建议功能
"""
import sys
sys.path.insert(0, 'habit_tracker')

from logic import get_weekly_heatmap, calculate_streak, calculate_completion_rate
from feedback import get_smart_feedback, predict_tomorrow
from storage import get_all_habits

print("=" * 60)
print("📊 功能测试：热力图和智能建议")
print("=" * 60)

habits = get_all_habits()
if not habits:
    print("没有习惯数据")
else:
    for habit in habits:
        print(f"\n📚 习惯: {habit['name']} (ID: {habit['id']})")
        print("-" * 50)
        
        # 热力图
        heatmap = get_weekly_heatmap(habit['id'])
        print("📅 本周打卡热力图:")
        for day in heatmap:
            status = "🟩" if day["checked"] else "⬜"
            print(f"  {status} {day['day']} ({day['date']})")
        
        checked_count = sum(1 for d in heatmap if d["checked"])
        print(f"  本周完成: {checked_count}/7 天")
        
        # 统计数据
        streak = calculate_streak(habit['id'])
        completion_rate = calculate_completion_rate(habit['id'])
        print(f"\n📈 统计数据:")
        print(f"  当前连续: {streak}天")
        print(f"  近7天完成率: {completion_rate*100:.1f}%")
        
        # 智能反馈
        print(f"\n💡 智能反馈:")
        print(get_smart_feedback(streak, completion_rate))

print("\n" + "=" * 60)
print("🔮 明日预测:")
print("=" * 60)
print(predict_tomorrow())

from datetime import datetime, timedelta
from storage import get_check_ins

def calculate_streak(habit_id):
    check_ins = get_check_ins(habit_id)
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

def calculate_completion_rate(habit_id, days=7):
    check_ins = get_check_ins(habit_id)
    if not check_ins:
        return 0.0
    
    dates = set(record["date"] for record in check_ins)
    
    today = datetime.now().date()
    total_days = 0
    completed_days = 0
    
    for i in range(days):
        check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        total_days += 1
        if check_date in dates:
            completed_days += 1
    
    return completed_days / total_days if total_days > 0 else 0.0

def get_weekly_heatmap(habit_id):
    check_ins = get_check_ins(habit_id)
    dates = set(record["date"] for record in check_ins)
    
    today = datetime.now().date()
    heatmap = []
    
    for i in range(6, -1, -1):
        check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        day_name = (today - timedelta(days=i)).strftime("%a")
        checked = check_date in dates
        heatmap.append({
            "date": check_date,
            "day": day_name,
            "checked": checked
        })
    
    return heatmap

def get_today_status(habit_id):
    check_ins = get_check_ins(habit_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    for record in check_ins:
        if record["date"] == today:
            return True, record["timestamp"]
    
    return False, None

def get_statistics(habit_id):
    check_ins = get_check_ins(habit_id)
    
    if not check_ins:
        return {
            "total_check_ins": 0,
            "streak": 0,
            "completion_rate_7d": 0.0,
            "first_check_in": None,
            "last_check_in": None
        }
    
    dates = sorted([record["date"] for record in check_ins])
    
    return {
        "total_check_ins": len(check_ins),
        "streak": calculate_streak(habit_id),
        "completion_rate_7d": calculate_completion_rate(habit_id),
        "first_check_in": dates[0] if dates else None,
        "last_check_in": dates[-1] if dates else None
    }

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import add_habit, delete_habit, get_all_habits, check_in, load_data, save_data
from logic import calculate_streak, get_weekly_heatmap, get_statistics, calculate_completion_rate, get_today_status
from feedback import get_smart_feedback, predict_tomorrow

app = FastAPI(
    title="智能微习惯追踪器 API",
    description="习惯追踪器的 REST API 接口，支持添加习惯、打卡、查看统计等功能",
    version="1.0.0"
)

class HabitCreate(BaseModel):
    name: str
    frequency: str = "daily"

class HabitResponse(BaseModel):
    id: str
    name: str
    frequency: str
    created_at: str
    streak: int
    checked_today: bool

class CheckInResponse(BaseModel):
    success: bool
    message: str
    streak: int
    feedback: str

class StatisticsResponse(BaseModel):
    total_check_ins: int
    streak: int
    completion_rate_7d: float
    first_check_in: Optional[str]
    last_check_in: Optional[str]

class HeatmapItem(BaseModel):
    date: str
    day: str
    checked: bool

def simulate_check_in(habit_id: str, date_str: str) -> bool:
    data = load_data()
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    for record in data["check_ins"][habit_id]:
        if record["date"] == date_str:
            return False
    
    record = {
        "date": date_str,
        "timestamp": f"{date_str} 10:00:00"
    }
    data["check_ins"][habit_id].append(record)
    save_data(data)
    return True

@app.get("/")
async def root():
    return {
        "message": "智能微习惯追踪器 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "GET /habits": "获取所有习惯",
            "POST /habits": "添加新习惯",
            "DELETE /habits/{habit_id}": "删除习惯",
            "POST /habits/{habit_id}/checkin": "今日打卡",
            "POST /habits/{habit_id}/checkin/{date}": "指定日期打卡（测试用）",
            "GET /habits/{habit_id}/stats": "获取习惯统计",
            "GET /habits/{habit_id}/heatmap": "获取本周热力图",
            "GET /suggestions": "获取智能建议",
            "POST /test/simulate-week": "模拟一周使用（测试用）",
            "POST /test/clear": "清空所有数据（测试用）"
        }
    }

@app.get("/habits", response_model=list[HabitResponse])
async def get_habits():
    habits = get_all_habits()
    result = []
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        streak = calculate_streak(habit["id"])
        result.append(HabitResponse(
            id=habit["id"],
            name=habit["name"],
            frequency=habit["frequency"],
            created_at=habit["created_at"],
            streak=streak,
            checked_today=checked
        ))
    return result

@app.post("/habits")
async def create_habit(habit: HabitCreate):
    if not habit.name.strip():
        raise HTTPException(status_code=400, detail="习惯名称不能为空")
    
    if habit.frequency not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="频率必须是 daily 或 weekly")
    
    success, habit_id = add_habit(habit.name, habit.frequency)
    if success:
        return {"success": True, "habit_id": habit_id, "message": "习惯添加成功"}
    else:
        raise HTTPException(status_code=500, detail="添加失败")

@app.delete("/habits/{habit_id}")
async def remove_habit(habit_id: str):
    if delete_habit(habit_id):
        return {"success": True, "message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="习惯不存在")

@app.post("/habits/{habit_id}/checkin", response_model=CheckInResponse)
async def check_in_today(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    success, message = check_in(habit_id)
    streak = calculate_streak(habit_id)
    completion_rate = calculate_completion_rate(habit_id)
    feedback = get_smart_feedback(streak, completion_rate)
    
    return CheckInResponse(
        success=success,
        message=message,
        streak=streak,
        feedback=feedback
    )

@app.post("/habits/{habit_id}/checkin/{date}")
async def check_in_date(habit_id: str, date: str):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    success = simulate_check_in(habit_id, date)
    if success:
        streak = calculate_streak(habit_id)
        return {"success": True, "message": f"打卡成功 ({date})", "streak": streak}
    else:
        return {"success": False, "message": "该日期已打卡"}

@app.get("/habits/{habit_id}/stats", response_model=StatisticsResponse)
async def get_habit_stats(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    stats = get_statistics(habit_id)
    return StatisticsResponse(**stats)

@app.get("/habits/{habit_id}/heatmap", response_model=list[HeatmapItem])
async def get_habit_heatmap(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    heatmap = get_weekly_heatmap(habit_id)
    return [HeatmapItem(**item) for item in heatmap]

@app.get("/suggestions")
async def get_suggestions():
    habits = get_all_habits()
    if not habits:
        return {"message": "还没有任何习惯", "suggestion": predict_tomorrow()}
    
    unchecked = []
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        if not checked:
            streak = calculate_streak(habit["id"])
            unchecked.append({
                "id": habit["id"],
                "name": habit["name"],
                "streak": streak
            })
    
    return {
        "unchecked_today": unchecked,
        "all_completed": len(unchecked) == 0,
        "prediction": predict_tomorrow()
    }

@app.post("/test/simulate-week")
async def simulate_week_usage():
    data = load_data()
    data["habits"] = []
    data["check_ins"] = {}
    save_data(data)
    
    success1, reading_id = add_habit("每天阅读30分钟", "daily")
    success2, exercise_id = add_habit("每周运动3次", "weekly")
    
    today = datetime.now().date()
    
    for i in range(6, -1, -1):
        if i != 3:
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            simulate_check_in(reading_id, date_str)
    
    simulate_check_in(exercise_id, (today - timedelta(days=5)).strftime("%Y-%m-%d"))
    simulate_check_in(exercise_id, (today - timedelta(days=2)).strftime("%Y-%m-%d"))
    
    reading_streak = calculate_streak(reading_id)
    
    return {
        "success": True,
        "message": "模拟一周使用完成",
        "habits": [
            {"id": reading_id, "name": "每天阅读30分钟", "frequency": "daily"},
            {"id": exercise_id, "name": "每周运动3次", "frequency": "weekly"}
        ],
        "reading_streak": reading_streak,
        "expected_streak": 3,
        "streak_correct": reading_streak == 3
    }

@app.post("/test/clear")
async def clear_all_data():
    data = {"habits": [], "check_ins": {}}
    save_data(data)
    return {"success": True, "message": "所有数据已清空"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

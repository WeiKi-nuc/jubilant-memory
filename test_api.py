#!/usr/bin/env python3
"""
FastAPI 测试接口 - 智能微习惯追踪器
供内网同事调用测试的独立 API 服务
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'habit_tracker'))

DATA_FILE = "habit_data.json"

app = FastAPI(
    title="智能微习惯追踪器 - 测试API",
    description="内网测试接口，提供完整的习惯追踪功能",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HabitCreate(BaseModel):
    name: str
    frequency: str = "daily"

class CheckInRequest(BaseModel):
    habit_id: str
    date: Optional[str] = None

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"habits": [], "check_ins": {}}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"habits": [], "check_ins": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True

def calculate_streak(habit_id):
    data = load_data()
    check_ins = data["check_ins"].get(habit_id, [])
    if not check_ins:
        return 0
    
    dates = sorted([r["date"] for r in check_ins], reverse=True)
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

def get_today_status(habit_id):
    data = load_data()
    check_ins = data["check_ins"].get(habit_id, [])
    today = datetime.now().strftime("%Y-%m-%d")
    for record in check_ins:
        if record["date"] == today:
            return True, record["timestamp"]
    return False, None

@app.get("/")
async def root():
    return {
        "message": "智能微习惯追踪器 API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/habits")
async def get_habits():
    data = load_data()
    result = []
    for habit in data["habits"]:
        checked, _ = get_today_status(habit["id"])
        streak = calculate_streak(habit["id"])
        result.append({
            **habit,
            "today_checked": checked,
            "streak": streak
        })
    return result

@app.post("/api/habits")
async def create_habit(habit: HabitCreate):
    if not habit.name.strip():
        raise HTTPException(400, "习惯名称不能为空")
    if habit.frequency not in ["daily", "weekly"]:
        raise HTTPException(400, "频率必须为 daily 或 weekly")
    
    data = load_data()
    habit_id = str(len(data["habits"]) + 1)
    new_habit = {
        "id": habit_id,
        "name": habit.name,
        "frequency": habit.frequency,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["habits"].append(new_habit)
    save_data(data)
    return {"success": True, "habit_id": habit_id, "name": habit.name}

@app.delete("/api/habits/{habit_id}")
async def delete_habit(habit_id: str):
    data = load_data()
    data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
    if habit_id in data["check_ins"]:
        del data["check_ins"][habit_id]
    save_data(data)
    return {"success": True, "habit_id": habit_id}

@app.post("/api/checkin")
async def checkin(habit_id: str = Query(...)):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    for record in data["check_ins"][habit_id]:
        if record["date"] == today:
            return {"success": False, "message": "今天已经打卡过了！"}
    
    data["check_ins"][habit_id].append({
        "date": today,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(data)
    
    streak = calculate_streak(habit_id)
    return {"success": True, "streak": streak, "message": "打卡成功！"}

@app.post("/api/checkin/date")
async def checkin_with_date(req: CheckInRequest):
    data = load_data()
    date_str = req.date or datetime.now().strftime("%Y-%m-%d")
    
    if req.habit_id not in data["check_ins"]:
        data["check_ins"][req.habit_id] = []
    
    for record in data["check_ins"][req.habit_id]:
        if record["date"] == date_str:
            return {"success": False, "date": date_str, "message": "该日期已打卡"}
    
    data["check_ins"][req.habit_id].append({
        "date": date_str,
        "timestamp": f"{date_str} 08:00:00"
    })
    save_data(data)
    
    streak = calculate_streak(req.habit_id)
    return {"success": True, "date": date_str, "streak": streak}

@app.get("/api/habits/{habit_id}/statistics")
async def get_statistics(habit_id: str):
    data = load_data()
    habit = next((h for h in data["habits"] if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(404, "习惯不存在")
    
    check_ins = data["check_ins"].get(habit_id, [])
    dates = sorted([r["date"] for r in check_ins])
    
    today = datetime.now().date()
    recent_dates = set()
    for i in range(7):
        recent_dates.add((today - timedelta(days=i)).strftime("%Y-%m-%d"))
    
    completed = sum(1 for d in dates if d in recent_dates)
    
    return {
        "habit_id": habit_id,
        "habit_name": habit["name"],
        "total_check_ins": len(check_ins),
        "streak": calculate_streak(habit_id),
        "completion_rate_7d": round(completed / 7 * 100, 1),
        "first_check_in": dates[0] if dates else None,
        "last_check_in": dates[-1] if dates else None
    }

@app.get("/api/habits/{habit_id}/heatmap")
async def get_heatmap(habit_id: str):
    data = load_data()
    check_ins = set(r["date"] for r in data["check_ins"].get(habit_id, []))
    
    today = datetime.now().date()
    heatmap = []
    for i in range(6, -1, -1):
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        heatmap.append({
            "date": date_str,
            "day": check_date.strftime("%a"),
            "checked": date_str in check_ins
        })
    return heatmap

@app.delete("/api/data/reset")
async def reset_data():
    save_data({"habits": [], "check_ins": {}})
    return {"success": True, "message": "数据已重置"}

@app.post("/api/test/simulate-week")
async def simulate_week():
    """模拟一周使用场景：阅读断签后恢复，运动打卡2次"""
    data = {"habits": [], "check_ins": {}}
    save_data(data)
    
    data = load_data()
    data["habits"] = [
        {"id": "1", "name": "每天阅读30分钟", "frequency": "daily", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"id": "2", "name": "每周运动3次", "frequency": "weekly", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    ]
    
    today = datetime.now().date()
    data["check_ins"] = {"1": [], "2": []}
    
    for i in range(6, 3, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        data["check_ins"]["1"].append({"date": d, "timestamp": f"{d} 08:00:00"})
    
    for i in range(2, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        data["check_ins"]["1"].append({"date": d, "timestamp": f"{d} 08:00:00"})
    
    for i in [5, 2]:
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        data["check_ins"]["2"].append({"date": d, "timestamp": f"{d} 08:00:00"})
    
    save_data(data)
    
    return {
        "success": True,
        "message": "模拟完成：阅读连续3天（中间断签），运动打卡2次",
        "reading_streak": calculate_streak("1"),
        "expected_streak": 3,
        "streak_correct": calculate_streak("1") == 3
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("启动测试API服务")
    print("=" * 50)
    print("文档: http://localhost:8000/docs")
    print("内网访问: http://<你的IP>:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uvicorn

from storage import add_habit, delete_habit, get_all_habits, check_in, load_data, save_data
from logic import calculate_streak, get_weekly_heatmap, get_statistics, calculate_completion_rate
from feedback import get_smart_feedback, predict_tomorrow

app = FastAPI(
    title="智能微习惯追踪器 API",
    description="习惯追踪器的RESTful API接口，供内网测试使用",
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

class CheckInRequest(BaseModel):
    habit_id: str
    date: Optional[str] = None

class CheckInResponse(BaseModel):
    success: bool
    message: str
    streak: int
    feedback: str

class StatisticsResponse(BaseModel):
    habit_id: str
    habit_name: str
    total_check_ins: int
    streak: int
    completion_rate_7d: float
    first_check_in: Optional[str]
    last_check_in: Optional[str]

class HeatmapDay(BaseModel):
    date: str
    day: str
    checked: bool

class HeatmapResponse(BaseModel):
    habit_id: str
    habit_name: str
    heatmap: list[HeatmapDay]
    completed_days: int
    total_days: int

class SmartSuggestionResponse(BaseModel):
    unchecked_habits: list[dict]
    prediction: str

def simulate_check_in(habit_id: str, date_str: str) -> tuple[bool, str]:
    data = load_data()
    
    for habit in data["habits"]:
        if habit["id"] == habit_id:
            break
    else:
        return False, "习惯不存在！"
    
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    for record in data["check_ins"][habit_id]:
        if record["date"] == date_str:
            return False, f"{date_str} 已经打卡过了！"
    
    record = {
        "date": date_str,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["check_ins"][habit_id].append(record)
    save_data(data)
    return True, f"{date_str} 打卡成功！"

@app.get("/", summary="API根路径")
async def root():
    return {
        "message": "智能微习惯追踪器 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "habits": "/api/habits",
            "check_in": "/api/check-in",
            "statistics": "/api/statistics/{habit_id}",
            "heatmap": "/api/heatmap/{habit_id}",
            "suggestion": "/api/suggestion"
        }
    }

@app.get("/api/habits", response_model=list[HabitResponse], summary="获取所有习惯")
async def get_habits():
    habits = get_all_habits()
    result = []
    for habit in habits:
        streak = calculate_streak(habit["id"])
        today = datetime.now().strftime("%Y-%m-%d")
        check_ins = load_data()["check_ins"].get(habit["id"], [])
        checked_today = any(r["date"] == today for r in check_ins)
        
        result.append(HabitResponse(
            id=habit["id"],
            name=habit["name"],
            frequency=habit["frequency"],
            created_at=habit["created_at"],
            streak=streak,
            checked_today=checked_today
        ))
    return result

@app.post("/api/habits", summary="添加新习惯")
async def create_habit(habit: HabitCreate):
    if not habit.name.strip():
        raise HTTPException(status_code=400, detail="习惯名称不能为空！")
    
    if habit.frequency not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="频率必须是 daily 或 weekly")
    
    success, habit_id = add_habit(habit.name, habit.frequency)
    if success:
        return {
            "success": True,
            "message": "习惯添加成功！",
            "habit_id": habit_id,
            "name": habit.name,
            "frequency": habit.frequency
        }
    else:
        raise HTTPException(status_code=500, detail="添加失败，请重试！")

@app.delete("/api/habits/{habit_id}", summary="删除习惯")
async def remove_habit(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在！")
    
    if delete_habit(habit_id):
        return {
            "success": True,
            "message": f"习惯 '{habit['name']}' 删除成功！"
        }
    else:
        raise HTTPException(status_code=500, detail="删除失败！")

@app.post("/api/check-in", response_model=CheckInResponse, summary="打卡")
async def do_check_in(request: CheckInRequest):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == request.habit_id), None)
    
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在！")
    
    date_str = request.date or datetime.now().strftime("%Y-%m-%d")
    
    success, message = simulate_check_in(request.habit_id, date_str)
    
    streak = calculate_streak(request.habit_id)
    completion_rate = calculate_completion_rate(request.habit_id)
    feedback = get_smart_feedback(streak, completion_rate)
    
    return CheckInResponse(
        success=success,
        message=message,
        streak=streak,
        feedback=feedback
    )

@app.get("/api/statistics/{habit_id}", response_model=StatisticsResponse, summary="获取习惯统计")
async def get_habit_statistics(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在！")
    
    stats = get_statistics(habit_id)
    
    return StatisticsResponse(
        habit_id=habit_id,
        habit_name=habit["name"],
        total_check_ins=stats["total_check_ins"],
        streak=stats["streak"],
        completion_rate_7d=stats["completion_rate_7d"],
        first_check_in=stats["first_check_in"],
        last_check_in=stats["last_check_in"]
    )

@app.get("/api/heatmap/{habit_id}", response_model=HeatmapResponse, summary="获取本周热力图")
async def get_habit_heatmap(habit_id: str):
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在！")
    
    heatmap = get_weekly_heatmap(habit_id)
    completed_days = sum(1 for d in heatmap if d["checked"])
    
    return HeatmapResponse(
        habit_id=habit_id,
        habit_name=habit["name"],
        heatmap=[HeatmapDay(**d) for d in heatmap],
        completed_days=completed_days,
        total_days=7
    )

@app.get("/api/suggestion", response_model=SmartSuggestionResponse, summary="获取智能建议")
async def get_suggestion():
    habits = get_all_habits()
    
    unchecked = []
    today = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    
    for habit in habits:
        check_ins = data["check_ins"].get(habit["id"], [])
        checked_today = any(r["date"] == today for r in check_ins)
        
        if not checked_today:
            streak = calculate_streak(habit["id"])
            unchecked.append({
                "id": habit["id"],
                "name": habit["name"],
                "streak": streak
            })
    
    return SmartSuggestionResponse(
        unchecked_habits=unchecked,
        prediction=predict_tomorrow()
    )

@app.post("/api/reset", summary="重置所有数据")
async def reset_data():
    data = {"habits": [], "check_ins": {}}
    save_data(data)
    return {"success": True, "message": "所有数据已重置！"}

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 50)
    print("[*] 启动智能微习惯追踪器 API 服务")
    print("=" * 50)
    print("[+] API文档: http://localhost:9000/docs")
    print("[+] 备用文档: http://localhost:9000/redoc")
    print("=" * 50)
    print("[!] 内网访问: 将 localhost 替换为本机IP地址")
    print("    例如: http://192.168.x.x:9000/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=9000)

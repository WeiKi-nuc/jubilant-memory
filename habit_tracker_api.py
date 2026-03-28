"""
习惯追踪器 FastAPI 接口
提供 RESTful API 供内网测试使用
"""
import sys
sys.path.insert(0, 'habit_tracker')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from storage import (
    add_habit, delete_habit, get_all_habits, check_in,
    load_data, save_data, get_check_ins
)
from logic import (
    calculate_streak, get_weekly_heatmap, get_today_status,
    get_statistics, calculate_completion_rate
)
from feedback import get_smart_feedback, predict_tomorrow

app = FastAPI(
    title="习惯追踪器 API",
    description="智能微习惯追踪器的 RESTful API 接口",
    version="1.0.0"
)

# 配置 CORS，允许内网访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（内网使用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 数据模型 ============

class HabitCreate(BaseModel):
    name: str
    frequency: str = "daily"  # daily 或 weekly


class HabitResponse(BaseModel):
    id: str
    name: str
    frequency: str
    created_at: str
    streak: int = 0
    checked_today: bool = False


class CheckInResponse(BaseModel):
    success: bool
    message: str
    streak: int
    feedback: Optional[str] = None


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
    heatmap: List[HeatmapDay]
    weekly_completion: str


class SmartSuggestionResponse(BaseModel):
    unchecked_habits: List[dict]
    all_completed: bool
    tomorrow_prediction: str


class SimulationRequest(BaseModel):
    days: int = 7
    reading_check_days: List[int] = [1, 2, 3, 5, 6, 7]  # 第4天不打
    exercise_check_days: List[int] = [2, 5]  # 运动打卡2次


# ============ API 路由 ============

@app.get("/")
def root():
    """API 根路径，返回基本信息"""
    return {
        "message": "习惯追踪器 API 服务运行中",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "habits": "/api/habits",
            "check_in": "/api/habits/{id}/checkin",
            "statistics": "/api/habits/{id}/statistics",
            "heatmap": "/api/habits/{id}/heatmap",
            "suggestions": "/api/suggestions",
            "simulation": "/api/simulation/run"
        }
    }


@app.get("/api/habits", response_model=List[HabitResponse])
def list_habits():
    """获取所有习惯列表"""
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


@app.post("/api/habits", response_model=HabitResponse)
def create_habit(habit: HabitCreate):
    """创建新习惯"""
    if not habit.name.strip():
        raise HTTPException(status_code=400, detail="习惯名称不能为空")
    
    if habit.frequency not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="频率必须是 daily 或 weekly")
    
    success, habit_id = add_habit(habit.name, habit.frequency)
    if not success:
        raise HTTPException(status_code=500, detail="创建习惯失败")
    
    habits = get_all_habits()
    new_habit = next((h for h in habits if h["id"] == habit_id), None)
    
    return HabitResponse(
        id=new_habit["id"],
        name=new_habit["name"],
        frequency=new_habit["frequency"],
        created_at=new_habit["created_at"],
        streak=0,
        checked_today=False
    )


@app.delete("/api/habits/{habit_id}")
def remove_habit(habit_id: str):
    """删除习惯"""
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    if delete_habit(habit_id):
        return {"success": True, "message": f"习惯 '{habit['name']}' 已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")


@app.post("/api/habits/{habit_id}/checkin", response_model=CheckInResponse)
def habit_check_in(habit_id: str):
    """今日打卡"""
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    success, message = check_in(habit_id)
    streak = calculate_streak(habit_id)
    
    if success:
        completion_rate = calculate_completion_rate(habit_id)
        feedback = get_smart_feedback(streak, completion_rate)
        return CheckInResponse(
            success=True,
            message=message,
            streak=streak,
            feedback=feedback
        )
    else:
        return CheckInResponse(
            success=False,
            message=message,
            streak=streak
        )


@app.get("/api/habits/{habit_id}/statistics", response_model=StatisticsResponse)
def habit_statistics(habit_id: str):
    """获取习惯统计信息"""
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
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


@app.get("/api/habits/{habit_id}/heatmap", response_model=HeatmapResponse)
def habit_heatmap(habit_id: str):
    """获取习惯热力图"""
    habits = get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail="习惯不存在")
    
    heatmap_data = get_weekly_heatmap(habit_id)
    heatmap = [HeatmapDay(**day) for day in heatmap_data]
    checked_count = sum(1 for d in heatmap_data if d["checked"])
    
    return HeatmapResponse(
        habit_id=habit_id,
        habit_name=habit["name"],
        heatmap=heatmap,
        weekly_completion=f"{checked_count}/7"
    )


@app.get("/api/suggestions", response_model=SmartSuggestionResponse)
def smart_suggestions():
    """获取智能建议"""
    habits = get_all_habits()
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
    
    return SmartSuggestionResponse(
        unchecked_habits=unchecked,
        all_completed=len(unchecked) == 0,
        tomorrow_prediction=predict_tomorrow()
    )


@app.post("/api/simulation/run")
def run_simulation(config: SimulationRequest):
    """
    运行一周使用模拟
    模拟用户的打卡行为，用于测试
    """
    # 重置数据
    data = {"habits": [], "check_ins": {}}
    save_data(data)
    
    # 创建习惯
    reading_success, reading_id = add_habit("每天阅读30分钟", "daily")
    exercise_success, exercise_id = add_habit("每周运动3次", "weekly")
    
    today = datetime.now().date()
    results = {
        "message": "模拟完成",
        "reading_habit": {"id": reading_id, "name": "每天阅读30分钟"},
        "exercise_habit": {"id": exercise_id, "name": "每周运动3次"},
        "daily_logs": [],
        "final_statistics": {}
    }
    
    # 模拟每一天
    for day_num in range(1, config.days + 1):
        date = today - timedelta(days=config.days - day_num)
        date_str = date.strftime("%Y-%m-%d")
        
        day_log = {"day": day_num, "date": date_str, "actions": []}
        
        # 阅读打卡
        if day_num in config.reading_check_days:
            data = load_data()
            if reading_id not in data["check_ins"]:
                data["check_ins"][reading_id] = []
            data["check_ins"][reading_id].append({
                "date": date_str,
                "timestamp": f"{date_str} 20:00:00"
            })
            save_data(data)
            day_log["actions"].append("阅读打卡 [OK]")
        else:
            day_log["actions"].append("阅读未打卡 [X]")
        
        # 运动打卡
        if day_num in config.exercise_check_days:
            data = load_data()
            if exercise_id not in data["check_ins"]:
                data["check_ins"][exercise_id] = []
            data["check_ins"][exercise_id].append({
                "date": date_str,
                "timestamp": f"{date_str} 20:00:00"
            })
            save_data(data)
            day_log["actions"].append("运动打卡 [OK]")
        
        results["daily_logs"].append(day_log)
    
    # 最终统计
    results["final_statistics"] = {
        "reading": {
            "total_check_ins": len(get_check_ins(reading_id)),
            "streak": calculate_streak(reading_id),
            "completion_rate": calculate_completion_rate(reading_id)
        },
        "exercise": {
            "total_check_ins": len(get_check_ins(exercise_id)),
            "streak": calculate_streak(exercise_id),
            "completion_rate": calculate_completion_rate(exercise_id)
        }
    }
    
    return results


@app.get("/api/data/raw")
def get_raw_data():
    """获取原始数据（用于调试）"""
    return load_data()


@app.delete("/api/data/reset")
def reset_data():
    """重置所有数据（谨慎使用）"""
    data = {"habits": [], "check_ins": {}}
    save_data(data)
    return {"success": True, "message": "数据已重置"}


# ============ 启动服务 ============

if __name__ == "__main__":
    import uvicorn
    
    PORT = 8765
    print("=" * 60)
    print("习惯追踪器 API 服务启动")
    print("=" * 60)
    print(f"API 文档地址: http://localhost:{PORT}/docs")
    print(f"API 基础地址: http://localhost:{PORT}/api")
    print("=" * 60)
    
    # 监听所有网络接口，允许内网访问
    uvicorn.run(app, host="0.0.0.0", port=PORT)

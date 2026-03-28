#!/usr/bin/env python3
"""
FastAPI 接口 for 智能微习惯追踪器
提供 RESTful API 供内网调用测试
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import sys
import os

# 导入现有模块
from storage import (
    add_habit as storage_add_habit,
    delete_habit as storage_delete_habit,
    get_all_habits as storage_get_all_habits,
    check_in as storage_check_in,
    get_check_ins,
    load_data,
    save_data
)
from logic import (
    calculate_streak,
    get_weekly_heatmap,
    get_today_status,
    get_statistics,
    calculate_completion_rate
)
from feedback import get_smart_feedback, predict_tomorrow

app = FastAPI(
    title="智能微习惯追踪器 API",
    description="供内网同事调用的习惯追踪器 RESTful API 接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS 允许内网访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境可限制为具体内网IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 模型
class HabitCreate(BaseModel):
    name: str
    frequency: str = "daily"  # daily 或 weekly

class CheckInWithDate(BaseModel):
    habit_id: str
    date: Optional[str] = None  # 格式: YYYY-MM-DD，默认为今天

class HabitResponse(BaseModel):
    id: str
    name: str
    frequency: str
    created_at: str
    today_checked: bool
    streak: int

class StatisticsResponse(BaseModel):
    habit_id: str
    habit_name: str
    total_check_ins: int
    streak: int
    completion_rate_7d: float
    first_check_in: Optional[str]
    last_check_in: Optional[str]

class HeatmapItem(BaseModel):
    date: str
    day: str
    checked: bool

# API 路由
@app.get("/", summary="API 根路径", description="返回 API 欢迎信息")
async def root():
    return {
        "message": "欢迎使用智能微习惯追踪器 API",
        "docs": "/docs (Swagger UI)",
        "redoc": "/redoc (ReDoc)",
        "version": "1.0.0"
    }

@app.get("/api/habits", summary="获取所有习惯", response_model=List[HabitResponse])
async def get_habits():
    """获取所有习惯及其今日状态和连续天数"""
    habits = storage_get_all_habits()
    result = []
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        streak = calculate_streak(habit["id"])
        result.append({
            "id": habit["id"],
            "name": habit["name"],
            "frequency": habit["frequency"],
            "created_at": habit["created_at"],
            "today_checked": checked,
            "streak": streak
        })
    return result

@app.post("/api/habits", summary="添加新习惯")
async def create_habit(habit: HabitCreate):
    """添加新习惯，支持 daily(每天) 或 weekly(每周)"""
    if not habit.name.strip():
        raise HTTPException(status_code=400, detail="习惯名称不能为空")
    
    if habit.frequency not in ["daily", "weekly"]:
        raise HTTPException(status_code=400, detail="频率必须为 daily 或 weekly")
    
    success, habit_id = storage_add_habit(habit.name, habit.frequency)
    if success:
        return {
            "success": True,
            "habit_id": habit_id,
            "name": habit.name,
            "frequency": habit.frequency,
            "message": "习惯添加成功"
        }
    raise HTTPException(status_code=500, detail="添加习惯失败，请重试")

@app.delete("/api/habits/{habit_id}", summary="删除习惯")
async def remove_habit(habit_id: str):
    """删除指定ID的习惯及其打卡记录"""
    if storage_delete_habit(habit_id):
        return {
            "success": True,
            "habit_id": habit_id,
            "message": "习惯删除成功"
        }
    raise HTTPException(status_code=404, detail=f"未找到ID为 {habit_id} 的习惯")

@app.post("/api/checkin", summary="今日打卡")
async def checkin(habit_id: str = Query(..., description="习惯ID")):
    """为指定习惯进行今日打卡，重复打卡会返回失败"""
    success, message = storage_check_in(habit_id)
    if success:
        streak = calculate_streak(habit_id)
        completion_rate = calculate_completion_rate(habit_id)
        feedback = get_smart_feedback(streak, completion_rate)
        return {
            "success": True,
            "habit_id": habit_id,
            "streak": streak,
            "completion_rate": round(completion_rate * 100, 1),
            "feedback": feedback,
            "message": message
        }
    return {
        "success": False,
        "habit_id": habit_id,
        "message": message
    }

@app.post("/api/checkin/date", summary="指定日期打卡（用于测试回溯）")
async def checkin_with_date(checkin_data: CheckInWithDate):
    """为指定日期打卡，用于测试回溯场景"""
    habit_id = checkin_data.habit_id
    date_str = checkin_data.date
    
    # 验证习惯是否存在
    habits = storage_get_all_habits()
    if not any(h["id"] == habit_id for h in habits):
        raise HTTPException(status_code=404, detail=f"未找到ID为 {habit_id} 的习惯")
    
    # 处理日期
    if date_str:
        try:
            check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
    else:
        check_date = datetime.now().date()
    
    date_str = check_date.strftime("%Y-%m-%d")
    
    # 检查是否已打卡
    data = load_data()
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    for record in data["check_ins"][habit_id]:
        if record["date"] == date_str:
            return {
                "success": False,
                "habit_id": habit_id,
                "date": date_str,
                "message": f"{date_str} 已经打卡过了"
            }
    
    # 添加打卡记录
    record = {
        "date": date_str,
        "timestamp": f"{date_str} 08:00:00"
    }
    data["check_ins"][habit_id].append(record)
    
    if save_data(data):
        streak = calculate_streak(habit_id)
        return {
            "success": True,
            "habit_id": habit_id,
            "date": date_str,
            "streak": streak,
            "message": "打卡成功"
        }
    
    raise HTTPException(status_code=500, detail="打卡失败")

@app.get("/api/habits/{habit_id}/statistics", summary="获取习惯统计信息", response_model=StatisticsResponse)
async def get_habit_statistics(habit_id: str):
    """获取指定习惯的详细统计信息"""
    habits = storage_get_all_habits()
    habit = next((h for h in habits if h["id"] == habit_id), None)
    if not habit:
        raise HTTPException(status_code=404, detail=f"未找到ID为 {habit_id} 的习惯")
    
    stats = get_statistics(habit_id)
    return {
        "habit_id": habit_id,
        "habit_name": habit["name"],
        "total_check_ins": stats["total_check_ins"],
        "streak": stats["streak"],
        "completion_rate_7d": round(stats["completion_rate_7d"] * 100, 1),
        "first_check_in": stats["first_check_in"],
        "last_check_in": stats["last_check_in"]
    }

@app.get("/api/habits/{habit_id}/heatmap", summary="获取本周热力图", response_model=List[HeatmapItem])
async def get_habit_heatmap(habit_id: str):
    """获取指定习惯近7天的打卡热力图"""
    habits = storage_get_all_habits()
    if not any(h["id"] == habit_id for h in habits):
        raise HTTPException(status_code=404, detail=f"未找到ID为 {habit_id} 的习惯")
    
    heatmap = get_weekly_heatmap(habit_id)
    return heatmap

@app.get("/api/smart-suggestions", summary="获取智能建议")
async def get_smart_suggestions():
    """获取智能建议，包括今日未打卡习惯提醒和明日建议"""
    habits = storage_get_all_habits()
    if not habits:
        return {
            "has_habits": False,
            "message": "还没有任何习惯，快去添加一个吧！",
            "unchecked_habits": [],
            "tomorrow_prediction": predict_tomorrow()
        }
    
    unchecked = []
    for habit in habits:
        checked, _ = get_today_status(habit["id"])
        if not checked:
            streak = calculate_streak(habit["id"])
            unchecked.append({
                "id": habit["id"],
                "name": habit["name"],
                "frequency": habit["frequency"],
                "streak": streak
            })
    
    return {
        "has_habits": True,
        "all_completed": len(unchecked) == 0,
        "unchecked_habits": unchecked,
        "completed_count": len(habits) - len(unchecked),
        "total_habits": len(habits),
        "tomorrow_prediction": predict_tomorrow()
    }

@app.delete("/api/data/reset", summary="重置所有数据（测试用）")
async def reset_all_data():
    """清除所有习惯和打卡记录，用于测试重置"""
    data = {
        "habits": [],
        "check_ins": {}
    }
    if save_data(data):
        return {
            "success": True,
            "message": "所有数据已重置"
        }
    raise HTTPException(status_code=500, detail="重置数据失败")

@app.get("/api/data/export", summary="导出所有数据")
async def export_data():
    """导出所有习惯和打卡数据"""
    data = load_data()
    return {
        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }

@app.post("/api/test/flow", summary="运行完整测试流程")
async def run_test_flow():
    """自动化运行完整的用户测试流程（用于快速验证）"""
    # 重置数据
    data = {
        "habits": [],
        "check_ins": {}
    }
    save_data(data)
    
    # 添加习惯
    _, reading_id = storage_add_habit("每天阅读30分钟", "daily")
    _, exercise_id = storage_add_habit("每周运动3次", "weekly")
    
    today = datetime.now().date()
    
    # 模拟一周打卡
    # 第1-3天: 阅读打卡
    for i in range(6, 3, -1):
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        data = load_data()
        if reading_id not in data["check_ins"]:
            data["check_ins"][reading_id] = []
        data["check_ins"][reading_id].append({
            "date": date_str,
            "timestamp": f"{date_str} 08:00:00"
        })
        save_data(data)
    
    # 第4天: 忘记打卡（跳过）
    
    # 第5-7天: 继续阅读打卡
    for i in range(2, -1, -1):
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        data = load_data()
        if reading_id not in data["check_ins"]:
            data["check_ins"][reading_id] = []
        data["check_ins"][reading_id].append({
            "date": date_str,
            "timestamp": f"{date_str} 08:00:00"
        })
        save_data(data)
    
    # 运动打卡2次
    for i in [5, 2]:
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        data = load_data()
        if exercise_id not in data["check_ins"]:
            data["check_ins"][exercise_id] = []
        data["check_ins"][exercise_id].append({
            "date": date_str,
            "timestamp": f"{date_str} 08:00:00"
        })
        save_data(data)
    
    # 获取统计
    reading_stats = get_statistics(reading_id)
    exercise_stats = get_statistics(exercise_id)
    
    # 验证 streak
    streak_correct = reading_stats["streak"] == 3
    
    return {
        "success": True,
        "message": "测试流程完成",
        "test_results": {
            "reading_streak": reading_stats["streak"],
            "expected_streak": 3,
            "streak_correct": streak_correct,
            "reading_total": reading_stats["total_check_ins"],
            "exercise_total": exercise_stats["total_check_ins"]
        },
        "habits_created": [
            {"id": reading_id, "name": "每天阅读30分钟"},
            {"id": exercise_id, "name": "每周运动3次"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 启动智能微习惯追踪器 API 服务")
    print("=" * 60)
    print(f"📖 Swagger UI: http://localhost:8000/docs")
    print(f"📚 ReDoc: http://localhost:8000/redoc")
    print(f"🔗 API 根路径: http://localhost:8000")
    print("=" * 60)
    print("💡 内网同事可通过你的IP地址访问: http://<你的IP>:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

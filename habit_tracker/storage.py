import json
import os
from datetime import datetime

DATA_FILE = "habit_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "habits": [],
            "check_ins": {}
        }
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "habits": [],
            "check_ins": {}
        }

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False

def add_habit(name, frequency="daily"):
    data = load_data()
    habit_id = str(len(data["habits"]) + 1)
    habit = {
        "id": habit_id,
        "name": name,
        "frequency": frequency,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["habits"].append(habit)
    return save_data(data), habit_id

def delete_habit(habit_id):
    data = load_data()
    data["habits"] = [h for h in data["habits"] if h["id"] != habit_id]
    if habit_id in data["check_ins"]:
        del data["check_ins"][habit_id]
    return save_data(data)

def get_all_habits():
    data = load_data()
    return data["habits"]

def check_in(habit_id):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if habit_id not in data["check_ins"]:
        data["check_ins"][habit_id] = []
    
    for record in data["check_ins"][habit_id]:
        if record["date"] == today:
            return False, "今天已经打卡过了！"
    
    record = {
        "date": today,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data["check_ins"][habit_id].append(record)
    return save_data(data), "打卡成功！"

def get_check_ins(habit_id):
    data = load_data()
    return data["check_ins"].get(habit_id, [])

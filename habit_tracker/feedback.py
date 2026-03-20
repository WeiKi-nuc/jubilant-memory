import random

MOTIVATIONAL_QUOTES = [
    "千里之行，始于足下。",
    "成功不是将来才有的，而是从决定去做的那一刻起，持续累积而成。",
    "每一个不曾起舞的日子，都是对生命的辜负。",
    "自律给我自由。",
    "坚持就是胜利。",
    "今天的努力，是明天的骄傲。",
    "习惯若不是最好的仆人，便就是最差的主人。",
    "优秀是一种习惯。",
    "行动是治愈恐惧的良药。",
    "不积跬步，无以至千里。"
]

def get_streak_feedback(streak_days):
    if streak_days == 0:
        return "开始你的第一天吧！"
    elif streak_days <= 3:
        messages = [
            "起步很棒，保持节奏！",
            "良好的开始是成功的一半！",
            "你已经迈出了第一步，继续加油！"
        ]
        return random.choice(messages)
    elif streak_days <= 10:
        messages = [
            "你已经进入状态了，继续加油！",
            "坚持得不错，你正在养成好习惯！",
            f"连续{streak_days}天！你的自律正在变强！"
        ]
        return random.choice(messages)
    else:
        messages = [
            "你是自律大师！🔥",
            f"太厉害了！{streak_days}天连续打卡！🏆",
            "你已经是一个习惯养成专家了！💪"
        ]
        return random.choice(messages)

def get_random_quote():
    return random.choice(MOTIVATIONAL_QUOTES)

def get_smart_feedback(streak_days, completion_rate=None):
    feedback = get_streak_feedback(streak_days)
    quote = get_random_quote()
    
    result = f"\n{feedback}\n"
    result += f"💡 名言警句：{quote}\n"
    
    if completion_rate is not None:
        if completion_rate >= 0.8:
            result += "📊 本周完成率很高，继续保持！\n"
        elif completion_rate >= 0.5:
            result += "📊 本周表现中等，还有提升空间！\n"
        else:
            result += "📊 本周完成率较低，明天记得打卡哦！\n"
    
    return result

def predict_tomorrow(recent_days=7):
    predictions = [
        "根据你的习惯，明天记得早起打卡哦！",
        "周末也不要忘记坚持好习惯！",
        "保持现在的节奏，你会越来越棒的！",
        "建议设置一个提醒，帮助自己按时打卡。",
        "坚持就是胜利，明天继续加油！"
    ]
    return random.choice(predictions)

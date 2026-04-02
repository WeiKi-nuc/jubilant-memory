"""
交互式界面测试 - 模拟用户体验
"""
import sys
sys.path.insert(0, 'habit_tracker')

from main import print_header, print_menu, view_habits
from storage import load_data

print_header()
print_menu()
print()
data = load_data()
print('当前数据文件状态:')
print(f'  习惯数量: {len(data["habits"])}')
print(f'  打卡记录: {len(data["check_ins"])} 个习惯')
view_habits()

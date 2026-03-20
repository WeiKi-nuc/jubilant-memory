#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from data_analyzer import DataAnalyzer
from log_reader import LogEntry, LogReader
from path_manager import PathManager
from report_generator import ReportGenerator


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="多格式日志文件分析与可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 分析所有日志文件
  python main.py --start 2024-01-01 # 分析指定日期之后的日志
  python main.py --level ERROR      # 仅分析 ERROR 级别日志
  python main.py --verbose          # 显示详细输出
        """
    )
    
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="基础路径（默认为当前目录）"
    )
    
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="开始时间（格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）"
    )
    
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="结束时间（格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）"
    )
    
    parser.add_argument(
        "--level",
        type=str,
        nargs="+",
        choices=["INFO", "WARN", "ERROR", "CRITICAL", "DEBUG"],
        help="仅分析指定级别的日志"
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="显示前 N 个高频项（默认: 10）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    return parser.parse_args()


def parse_time_arg(time_str: Optional[str]) -> Optional[datetime]:
    """解析时间参数。"""
    if not time_str:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    print(f"警告: 无法解析时间参数 '{time_str}'，将忽略此参数")
    return None


def print_banner() -> None:
    """打印程序横幅。"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║         多格式日志文件分析与可视化工具 v1.0              ║
    ║         Log File Analyzer & Visualizer                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main() -> int:
    """主函数。"""
    args = parse_args()
    
    print_banner()
    
    path_manager = PathManager(args.base_path)
    
    valid, error = path_manager.validate_input_dir()
    if not valid:
        print(f"错误: {error}")
        return 1
    
    valid, msg = path_manager.validate_protected_file()
    if args.verbose:
        print(f"受保护文件校验: {msg}")
    
    if not path_manager.ensure_output_dir():
        print("错误: 无法创建输出目录")
        return 1
    
    log_files = path_manager.get_log_files()
    if not log_files:
        print(f"警告: 输入目录 '{path_manager.input_dir}' 中未找到日志文件")
        print("支持的格式: .log, .jsonl")
        return 0
    
    print(f"发现 {len(log_files)} 个日志文件:")
    for f in log_files:
        protected_mark = " [受保护]" if path_manager.is_protected_file(f) else ""
        print(f"  - {f.name}{protected_mark}")
    print()
    
    reader = LogReader()
    entries: List[LogEntry] = list(reader.read_files(log_files))
    
    print(f"共读取 {len(entries)} 条日志记录")
    
    start_time = parse_time_arg(args.start)
    end_time = parse_time_arg(args.end)
    
    analyzer = DataAnalyzer(top_n=args.top_n)
    
    if start_time or end_time:
        entries = analyzer.filter_by_time_range(entries, start_time, end_time)
        print(f"时间过滤后: {len(entries)} 条记录")
    
    if args.level:
        entries = analyzer.filter_by_level(entries, args.level)
        print(f"级别过滤后: {len(entries)} 条记录")
    
    if not entries:
        print("警告: 过滤后无日志记录可分析")
        return 0
    
    print("\n正在分析日志数据...")
    result = analyzer.analyze(entries)
    
    print(f"分析完成:")
    print(f"  - 总条目: {result.total_entries}")
    print(f"  - 错误级别分布: {result.level_stats.to_dict()}")
    print(f"  - 高频错误数: {len(result.top_errors)}")
    
    valid, msg = path_manager.verify_protected_file_unchanged()
    if not valid:
        print(f"警告: {msg}")
    
    print("\n正在生成报告...")
    generator = ReportGenerator()
    success, msg = generator.save_reports(
        result,
        path_manager.output_txt_path,
        path_manager.output_json_path
    )
    
    print(msg)
    
    if args.verbose:
        print("\n" + "=" * 70)
        print("报告预览:")
        print("=" * 70)
        print(generator.generate_txt_report(result))
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
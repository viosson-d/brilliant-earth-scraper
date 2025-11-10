#!/usr/bin/env python3
"""
实时爬虫监控仪表板
显示爬虫进度、速率、成功率等信息
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import subprocess

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    """清屏"""
    os.system('clear' if os.name == 'posix' else 'cls')


def format_size(bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"


def get_process_info():
    """获取爬虫进程信息"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        crawlers = {
            'distributed': 0,
            'fast': 0,
            'fixed': 0,
            'other': 0,
        }
        
        for line in lines:
            if 'distributed_crawler' in line:
                crawlers['distributed'] += 1
            elif 'website_crawler_fast' in line:
                crawlers['fast'] += 1
            elif 'website_crawler_fixed' in line:
                crawlers['fixed'] += 1
            elif 'python' in line and 'crawler' in line.lower():
                crawlers['other'] += 1
        
        return crawlers
    except:
        return {}


def get_log_stats(log_file):
    """从日志文件获取统计信息"""
    stats = {
        'lines': 0,
        'errors': 0,
        'warnings': 0,
        'products': 0,
        'last_update': None,
    }
    
    if not os.path.exists(log_file):
        return stats
    
    try:
        with open(log_file, 'r', errors='ignore') as f:
            lines = f.readlines()
            stats['lines'] = len(lines)
            
            for line in lines:
                if 'ERROR' in line:
                    stats['errors'] += 1
                elif 'WARNING' in line:
                    stats['warnings'] += 1
                elif '发现' in line and '个产品' in line:
                    # 尝试提取产品数
                    try:
                        parts = line.split('发现')
                        if len(parts) > 1:
                            num_str = parts[1].split('个')[0].strip()
                            stats['products'] += int(num_str)
                    except:
                        pass
            
            if lines:
                stats['last_update'] = lines[-1][:19]  # 时间戳
    except:
        pass
    
    return stats


def get_results_summary():
    """获取结果摘要"""
    results_file = Path('crawler_data/crawl_results.json')
    
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                return {
                    'total_products': data.get('total_products', 0),
                    'elapsed': data.get('elapsed_seconds', 0),
                    'categories': len(data.get('by_category', {})),
                }
        except:
            pass
    
    return None


def get_disk_usage():
    """获取磁盘使用情况"""
    try:
        result = subprocess.run(['du', '-sh', 'products'], capture_output=True, text=True)
        return result.stdout.split()[0] if result.stdout else "0B"
    except:
        return "0B"


def get_file_count():
    """获取文件数"""
    try:
        count = len(list(Path('products').rglob('*')))
        return count
    except:
        return 0


def print_header():
    """打印标题"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "爬虫系统实时监控仪表板" + " "*24 + "║")
    print("╚" + "═"*78 + "╝")
    print(f"{Colors.ENDC}")


def print_process_status():
    """打印进程状态"""
    print(f"\n{Colors.BOLD}【进程状态】{Colors.ENDC}")
    print("─" * 80)
    
    processes = get_process_info()
    
    if processes.get('distributed'):
        print(f"  ✓ 分布式爬虫: {Colors.GREEN}运行中{Colors.ENDC}")
    else:
        print(f"  ✗ 分布式爬虫: {Colors.RED}未运行{Colors.ENDC}")
    
    if processes.get('fast'):
        print(f"  ✓ 快速爬虫: {Colors.GREEN}运行中{Colors.ENDC}")
    else:
        print(f"  ✗ 快速爬虫: {Colors.RED}未运行{Colors.ENDC}")
    
    if processes.get('fixed'):
        print(f"  ✓ 固定爬虫: {Colors.GREEN}运行中{Colors.ENDC}")
    else:
        print(f"  ✗ 固定爬虫: {Colors.RED}未运行{Colors.ENDC}")


def print_log_analysis():
    """打印日志分析"""
    print(f"\n{Colors.BOLD}【日志分析】{Colors.ENDC}")
    print("─" * 80)
    
    log_files = [
        ('distributed', 'crawler_logs/distributed_crawler.log'),
        ('fast', 'crawler_logs/fast_crawler.log'),
        ('fixed', 'crawler_logs/fixed_crawler.log'),
    ]
    
    total_products = 0
    total_errors = 0
    total_warnings = 0
    
    for name, log_file in log_files:
        if os.path.exists(log_file):
            stats = get_log_stats(log_file)
            total_products += stats['products']
            total_errors += stats['errors']
            total_warnings += stats['warnings']
            
            status = f"{Colors.GREEN}✓{Colors.ENDC}" if stats['lines'] > 0 else f"{Colors.RED}✗{Colors.ENDC}"
            print(f"  {status} {name:12} | 行数: {stats['lines']:6} | "
                  f"产品: {stats['products']:4} | "
                  f"错误: {stats['errors']:3} | "
                  f"警告: {stats['warnings']:3}")


def print_results_summary():
    """打印结果摘要"""
    print(f"\n{Colors.BOLD}【结果统计】{Colors.ENDC}")
    print("─" * 80)
    
    results = get_results_summary()
    if results:
        print(f"  总产品数: {Colors.GREEN}{results['total_products']}{Colors.ENDC}")
        print(f"  分类数: {results['categories']}")
        print(f"  耗时: {results['elapsed']/60:.1f} 分钟")
    else:
        print("  (尚无结果)")
    
    # 磁盘使用
    size = get_disk_usage()
    files = get_file_count()
    print(f"  已下载: {files} 个文件, {size}")


def print_time_info():
    """打印时间信息"""
    print(f"\n{Colors.BOLD}【系统信息】{Colors.ENDC}")
    print("─" * 80)
    print(f"  当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  更新间隔: 5秒")
    print(f"  日志目录: ./crawler_logs/")
    print(f"  结果目录: ./crawler_data/")
    print(f"  产品目录: ./products/")


def print_commands():
    """打印命令提示"""
    print(f"\n{Colors.BOLD}【命令提示】{Colors.ENDC}")
    print("─" * 80)
    print("  实时日志:    tail -f crawler_logs/distributed_crawler.log")
    print("  查看结果:    cat crawler_data/crawl_results.json | python3 -m json.tool")
    print("  杀死爬虫:    pkill -f crawler")
    print("  按 Ctrl+C 停止监控")


def main():
    """主循环"""
    try:
        iteration = 0
        while True:
            iteration += 1
            clear_screen()
            
            print_header()
            print_process_status()
            print_log_analysis()
            print_results_summary()
            print_time_info()
            print_commands()
            
            print(f"\n{Colors.YELLOW}[第{iteration}次更新]{Colors.ENDC}")
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}监控已停止{Colors.ENDC}")
        sys.exit(0)


if __name__ == '__main__':
    main()

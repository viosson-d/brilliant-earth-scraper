#!/usr/bin/env python3
"""
爬虫进度快速查看 - 实时更新
"""

import json
import os
import time
import sys
from pathlib import Path
from datetime import datetime

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_product_count():
    """获取产品总数"""
    try:
        with open('crawler_data/crawl_results.json', 'r') as f:
            data = json.load(f)
            return data.get('total_products', 0), data.get('elapsed_seconds', 0)
    except:
        return 0, 0

def get_file_stats():
    """获取文件统计"""
    try:
        products_dir = Path('products')
        if products_dir.exists():
            files = list(products_dir.rglob('*'))
            size = sum(f.stat().st_size for f in files if f.is_file())
            return len([f for f in files if f.is_file()]), size
        return 0, 0
    except:
        return 0, 0

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"

def main():
    iteration = 0
    try:
        while True:
            iteration += 1
            clear_screen()
            
            print("\n" + "="*60)
            print("🚀 爬虫系统实时进度")
            print("="*60)
            
            products, elapsed = get_product_count()
            files, size = get_file_stats()
            
            print(f"\n📊 爬虫数据:")
            print(f"  • 发现产品数: {products:,}")
            print(f"  • 已用时间: {elapsed/60:.1f} 分钟")
            
            print(f"\n💾 文件统计:")
            print(f"  • 文件数: {files:,}")
            print(f"  • 总大小: {format_size(size)}")
            
            print(f"\n⏱️  时间: {datetime.now().strftime('%H:%M:%S')}")
            print(f"📈 更新: 第{iteration}次")
            
            print("\n💡 命令:")
            print("  查看详细日志: tail -f crawler_logs/crawler_main.log")
            print("  完整仪表板: python3 monitor_dashboard.py")
            print("  停止爬虫: pkill -f crawler")
            
            print("\n" + "="*60)
            print("更新中... (5秒后刷新, 按Ctrl+C停止)\n")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n✓ 进度查看已停止")

if __name__ == '__main__':
    main()

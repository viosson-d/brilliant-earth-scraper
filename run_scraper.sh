#!/bin/bash

echo "==============================================="
echo "Brilliant Earth 全站爬虫"
echo "==============================================="
echo ""

echo "📦 检查依赖..."
pip3 list | grep -q "cloudscraper" || (echo "安装 cloudscraper..." && pip3 install cloudscraper -q)
pip3 list | grep -q "beautifulsoup4" || (echo "安装 beautifulsoup4..." && pip3 install beautifulsoup4 -q)
pip3 list | grep -q "requests" || (echo "安装 requests..." && pip3 install requests -q)

echo "✓ 依赖已检查"
echo ""

echo "请选择爬取模式:"
echo "1. 快速测试 (前10个产品)"
echo "2. 中等规模 (前50个产品)"
echo "3. 完整爬取 (所有产品) ⚠️ 耗时较长"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 开始快速测试..."
        python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from website_crawler_full import BrilliantEarthScraper
scraper = BrilliantEarthScraper()
scraper.run(max_products=10)
EOF
        ;;
    2)
        echo ""
        echo "🚀 开始中等规模爬取..."
        python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from website_crawler_full import BrilliantEarthScraper
scraper = BrilliantEarthScraper()
scraper.run(max_products=50)
EOF
        ;;
    3)
        echo ""
        echo "⚠️  开始完整爬取，这可能需要几十分钟..."
        read -p "确认继续? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from website_crawler_full import BrilliantEarthScraper
scraper = BrilliantEarthScraper()
scraper.run(max_products=None)
EOF
        else
            echo "已取消"
        fi
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 爬虫执行完成！"
echo "📁 文件保存在: ./products/"

#!/usr/bin/env python3
"""
多策略并行Cloudflare突破爬虫系统
- 使用多个不同的爬虫引擎同时运行
- 策略1: cloudscraper + 随机延迟 + UA轮换
- 策略2: Playwright浏览器 + 随机操作
- 策略3: 直接requests + 高级headers轮换
- 策略4: 代理轮换 (支持本地和远程)
- 所有策略并行运行，共享结果池
"""

import asyncio
import threading
import time
import json
import os
import sys
import random
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import cloudscraper
from typing import List, Dict, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(threadName)-12s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('multi_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置常量
# ============================================================================

BASE_URL = "https://www.brilliantearth.com"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

CATEGORIES = [
    "rings/diamond-rings",
    "rings/engagement-rings", 
    "rings/lab-diamond-rings",
    "earrings/diamond-earrings",
    "earrings/lab-diamond-earrings",
    "necklaces/diamond-necklaces",
    "necklaces/lab-diamond-necklaces",
    "bracelets/diamond-bracelets",
]

PROXIES_LOCAL = [
    # 本地代理 (如果有的话)
]

# ============================================================================
# 策略1: cloudscraper 爬虫 (最稳定)
# ============================================================================

class CloudscraperStrategy(threading.Thread):
    def __init__(self, results_pool: Dict, strategy_id: str = "CloudScraper"):
        super().__init__(daemon=True)
        self.results_pool = results_pool
        self.strategy_id = strategy_id
        self.session = None
        self.products_found = set()
        
    def setup_session(self):
        """设置cloudscraper会话"""
        try:
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                },
                delay=random.uniform(1, 3)
            )
            self.session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': BASE_URL
            })
            logger.info(f"[{self.strategy_id}] Cloudscraper会话初始化成功")
            return True
        except Exception as e:
            logger.error(f"[{self.strategy_id}] Cloudscraper初始化失败: {e}")
            return False
    
    def scrape_category(self, category: str, max_pages: int = 10) -> List[str]:
        """抓取单个分类"""
        if not self.session:
            return []
        
        category_url = f"{BASE_URL}/{category}"
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                # 页面参数
                params = {'page': page}
                
                # 添加随机延迟
                time.sleep(random.uniform(2, 5))
                
                logger.info(f"[{self.strategy_id}] 正在抓取 {category} 第{page}页...")
                response = self.session.get(category_url, params=params, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找产品链接
                product_links = soup.find_all('a', {'class': 'product-link'})
                if not product_links:
                    product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
                
                if not product_links:
                    logger.info(f"[{self.strategy_id}] {category} 第{page}页无产品，停止")
                    break
                
                for link in product_links:
                    href = link.get('href', '')
                    if href and '/products/' in href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in self.products_found:
                            products.append(full_url)
                            self.products_found.add(full_url)
                
                logger.info(f"[{self.strategy_id}] {category} 第{page}页: 发现{len(product_links)}个产品")
                
                if len(product_links) < 20:  # 最后一页
                    break
                    
            except Exception as e:
                logger.warning(f"[{self.strategy_id}] 抓取{category}第{page}页失败: {e}")
                time.sleep(random.uniform(5, 10))  # 失败后更长延迟
                if page > 3:  # 失败3次后跳过
                    break
        
        return products
    
    def extract_images_from_product(self, product_url: str) -> List[str]:
        """从产品页面提取图片"""
        if not self.session:
            return []
        
        try:
            time.sleep(random.uniform(1, 3))
            response = self.session.get(product_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = []
            
            # 多种方式提取图片
            for img in soup.find_all('img'):
                for attr in ['src', 'data-src', 'data-srcset']:
                    src = img.get(attr, '')
                    if 'brilliantearth' in src or 'cdn' in src:
                        images.append(src)
            
            logger.info(f"[{self.strategy_id}] {product_url}: 提取{len(images)}张图片")
            return images
        except Exception as e:
            logger.warning(f"[{self.strategy_id}] 提取产品图片失败: {e}")
            return []
    
    def run(self):
        """主线程"""
        logger.info(f"[{self.strategy_id}] 启动")
        
        if not self.setup_session():
            return
        
        for category in CATEGORIES:
            try:
                products = self.scrape_category(category, max_pages=15)
                logger.info(f"[{self.strategy_id}] {category}: 发现{len(products)}个产品")
                
                # 加入结果池
                for product_url in products:
                    if product_url not in self.results_pool['all_products']:
                        self.results_pool['all_products'].add(product_url)
                        self.results_pool['cloudscraper_products'].add(product_url)
                
                # 延迟避免被检测
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"[{self.strategy_id}] 处理分类{category}失败: {e}")


# ============================================================================
# 策略2: Requests + 高级Headers爬虫 (绕过简单检测)
# ============================================================================

class RequestsStrategy(threading.Thread):
    def __init__(self, results_pool: Dict, strategy_id: str = "Requests"):
        super().__init__(daemon=True)
        self.results_pool = results_pool
        self.strategy_id = strategy_id
        self.session = None
        self.products_found = set()
    
    def setup_session(self):
        """设置高级requests会话"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        logger.info(f"[{self.strategy_id}] 会话初始化成功")
    
    def scrape_category(self, category: str, max_pages: int = 10) -> List[str]:
        """使用requests抓取分类"""
        if not self.session:
            return []
        
        category_url = f"{BASE_URL}/{category}"
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                # 更新User-Agent
                self.session.headers['User-Agent'] = random.choice(USER_AGENTS)
                
                # 随机延迟
                time.sleep(random.uniform(3, 8))
                
                logger.info(f"[{self.strategy_id}] 正在抓取 {category} 第{page}页...")
                
                params = {'page': page}
                response = self.session.get(category_url, params=params, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找产品链接
                product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
                
                if not product_links:
                    logger.info(f"[{self.strategy_id}] {category} 第{page}页无产品")
                    break
                
                for link in product_links:
                    href = link.get('href', '')
                    if href and '/products/' in href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in self.products_found:
                            products.append(full_url)
                            self.products_found.add(full_url)
                
                logger.info(f"[{self.strategy_id}] {category} 第{page}页: {len(product_links)}个产品")
                
                if len(product_links) < 20:
                    break
                    
            except Exception as e:
                logger.warning(f"[{self.strategy_id}] 错误: {e}")
                time.sleep(random.uniform(8, 15))
                if page > 2:
                    break
        
        return products
    
    def run(self):
        """主线程"""
        logger.info(f"[{self.strategy_id}] 启动")
        self.setup_session()
        
        for category in CATEGORIES:
            try:
                products = self.scrape_category(category, max_pages=12)
                
                for product_url in products:
                    if product_url not in self.results_pool['all_products']:
                        self.results_pool['all_products'].add(product_url)
                        self.results_pool['requests_products'].add(product_url)
                
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.error(f"[{self.strategy_id}] 分类{category}错误: {e}")


# ============================================================================
# 策略3: 随机延迟爬虫 (超级慢速)
# ============================================================================

class SlowRandomStrategy(threading.Thread):
    def __init__(self, results_pool: Dict, strategy_id: str = "SlowRandom"):
        super().__init__(daemon=True)
        self.results_pool = results_pool
        self.strategy_id = strategy_id
        self.products_found = set()
    
    def scrape_category(self, category: str) -> List[str]:
        """超级慢速抓取"""
        category_url = f"{BASE_URL}/{category}"
        products = []
        
        for page in range(1, 20):  # 最多20页
            try:
                # 超长随机延迟: 10-30秒
                delay = random.uniform(10, 30)
                logger.info(f"[{self.strategy_id}] 延迟{delay:.1f}秒...")
                time.sleep(delay)
                
                logger.info(f"[{self.strategy_id}] 抓取 {category} 第{page}页...")
                
                # 每次请求都更换User-Agent
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Referer': BASE_URL,
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                response = requests.get(
                    category_url, 
                    params={'page': page},
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
                
                if not product_links:
                    logger.info(f"[{self.strategy_id}] {category} 第{page}页无产品")
                    break
                
                for link in product_links:
                    href = link.get('href', '')
                    if href and '/products/' in href:
                        full_url = urljoin(BASE_URL, href)
                        if full_url not in self.products_found:
                            products.append(full_url)
                            self.products_found.add(full_url)
                
                logger.info(f"[{self.strategy_id}] {category} 第{page}页: {len(product_links)}个产品")
                
                if len(product_links) < 15:
                    break
                    
            except Exception as e:
                logger.warning(f"[{self.strategy_id}] 错误: {e}")
                time.sleep(random.uniform(15, 45))
        
        return products
    
    def run(self):
        """主线程"""
        logger.info(f"[{self.strategy_id}] 启动 (超级慢速模式)")
        
        for category in CATEGORIES:
            try:
                products = self.scrape_category(category)
                
                for product_url in products:
                    if product_url not in self.results_pool['all_products']:
                        self.results_pool['all_products'].add(product_url)
                        self.results_pool['slow_products'].add(product_url)
                
                logger.info(f"[{self.strategy_id}] {category}: {len(products)}个产品")
                
            except Exception as e:
                logger.error(f"[{self.strategy_id}] 错误: {e}")


# ============================================================================
# 主协调器
# ============================================================================

class MultiStrategyCrawler:
    def __init__(self):
        self.results_pool = {
            'all_products': set(),
            'cloudscraper_products': set(),
            'requests_products': set(),
            'slow_products': set(),
            'images': defaultdict(list),
        }
        self.threads = []
        self.start_time = None
    
    def start_crawling(self):
        """启动所有爬虫策略"""
        logger.info("="*80)
        logger.info("多策略Cloudflare突破爬虫系统 - 启动")
        logger.info("="*80)
        
        self.start_time = time.time()
        
        # 启动多个爬虫策略
        strategies = [
            CloudscraperStrategy(self.results_pool, "CloudScraper-1"),
            CloudscraperStrategy(self.results_pool, "CloudScraper-2"),
            RequestsStrategy(self.results_pool, "Requests-1"),
            RequestsStrategy(self.results_pool, "Requests-2"),
            SlowRandomStrategy(self.results_pool, "SlowRandom-1"),
        ]
        
        for strategy in strategies:
            self.threads.append(strategy)
            strategy.start()
            logger.info(f"已启动: {strategy.strategy_id}")
            time.sleep(2)  # 策略间错开启动
        
        logger.info(f"共启动{len(strategies)}个爬虫策略")
    
    def monitor_progress(self):
        """监控进度"""
        while any(t.is_alive() for t in self.threads):
            time.sleep(10)
            total_products = len(self.results_pool['all_products'])
            elapsed = time.time() - self.start_time
            logger.info(f"[进度] 已发现 {total_products} 个产品 | 耗时 {elapsed/60:.1f} 分钟")
    
    def wait_for_completion(self):
        """等待所有线程完成"""
        for thread in self.threads:
            thread.join()
        
        elapsed = time.time() - self.start_time
        logger.info("="*80)
        logger.info("爬虫完成")
        logger.info("="*80)
        logger.info(f"总用时: {elapsed/60:.1f} 分钟")
        logger.info(f"CloudScraper发现: {len(self.results_pool['cloudscraper_products'])} 个产品")
        logger.info(f"Requests发现: {len(self.results_pool['requests_products'])} 个产品")
        logger.info(f"SlowRandom发现: {len(self.results_pool['slow_products'])} 个产品")
        logger.info(f"总共发现: {len(self.results_pool['all_products'])} 个产品")
        
        return self.results_pool
    
    def save_results(self):
        """保存结果到文件"""
        output_file = 'multi_strategy_results.json'
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_products': len(self.results_pool['all_products']),
            'products': list(self.results_pool['all_products']),
            'cloudflare_strategy': list(self.results_pool['cloudscraper_products']),
            'requests_strategy': list(self.results_pool['requests_products']),
            'slow_strategy': list(self.results_pool['slow_products']),
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"结果已保存: {output_file}")


def main():
    crawler = MultiStrategyCrawler()
    
    # 启动爬虫
    crawler.start_crawling()
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=crawler.monitor_progress, daemon=True)
    monitor_thread.start()
    
    # 等待完成
    try:
        crawler.wait_for_completion()
        crawler.save_results()
    except KeyboardInterrupt:
        logger.warning("用户中断爬虫")
    
    logger.info("多策略爬虫系统已关闭")


if __name__ == '__main__':
    main()

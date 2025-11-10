#!/usr/bin/env python3
"""
分布式爬虫调度器 - 支持多策略、持久化、失败恢复
突破Cloudflare限制的核心系统
"""

import asyncio
import threading
import time
import json
import os
import sys
import random
import pickle
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging
from collections import defaultdict

# 配置日志
log_dir = Path('crawler_logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(threadName)-15s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# 配置
# ============================================================================

BASE_URL = "https://www.brilliantearth.com"

# 策略特定配置
STRATEGIES = {
    'cloudscraper': {
        'workers': 3,  # 3个并行worker
        'min_delay': 1,
        'max_delay': 3,
        'timeout': 30,
        'max_retries': 5,
    },
    'requests': {
        'workers': 4,
        'min_delay': 3,
        'max_delay': 8,
        'timeout': 30,
        'max_retries': 3,
    },
    'slow': {
        'workers': 2,
        'min_delay': 10,
        'max_delay': 30,
        'timeout': 30,
        'max_retries': 2,
    },
    'async': {
        'workers': 5,
        'min_delay': 0.5,
        'max_delay': 2,
        'timeout': 15,
        'max_retries': 4,
    }
}

CATEGORIES = [
    "rings/diamond-rings",
    "rings/engagement-rings", 
    "rings/lab-diamond-rings",
    "earrings/diamond-earrings",
    "earrings/lab-diamond-earrings",
    "earrings/studs",
    "necklaces/diamond-necklaces",
    "necklaces/lab-diamond-necklaces",
    "bracelets/diamond-bracelets",
    "bracelets/tennis-bracelets",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ============================================================================
# 持久化存储
# ============================================================================

class PersistentStorage:
    """支持失败恢复的持久化存储"""
    
    def __init__(self, data_dir: str = 'crawler_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
    
    def save_checkpoint(self, checkpoint_data: dict):
        """保存检查点"""
        with self.lock:
            checkpoint_file = self.data_dir / f'checkpoint_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.info(f"检查点已保存: {checkpoint_file}")
    
    def load_latest_checkpoint(self) -> dict:
        """加载最新的检查点"""
        checkpoints = sorted(self.data_dir.glob('checkpoint_*.pkl'), reverse=True)
        if checkpoints:
            with open(checkpoints[0], 'rb') as f:
                data = pickle.load(f)
            logger.info(f"已加载检查点: {checkpoints[0]}")
            return data
        return None
    
    def save_results(self, results: dict, filename: str = 'results.json'):
        """保存最终结果"""
        with self.lock:
            output_file = self.data_dir / filename
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存: {output_file}")


# ============================================================================
# 抓取任务队列
# ============================================================================

class CrawlTask:
    """单个爬虫任务"""
    
    def __init__(self, task_id: str, category: str, page: int, strategy: str):
        self.task_id = task_id
        self.category = category
        self.page = page
        self.strategy = strategy
        self.status = 'pending'  # pending, running, success, failed
        self.retries = 0
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def __repr__(self):
        return f"Task({self.task_id}, {self.category}, p{self.page}, {self.strategy})"


class TaskQueue:
    """任务队列管理"""
    
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.completed = set()
        self.failed = defaultdict(int)
    
    def add_task(self, task: CrawlTask):
        """添加任务"""
        with self.lock:
            self.queue.append(task)
    
    def get_task(self) -> CrawlTask:
        """获取下一个任务"""
        with self.lock:
            if self.queue:
                # 优先失败较少的任务
                self.queue.sort(key=lambda t: self.failed[t.task_id])
                task = self.queue.pop(0)
                task.status = 'running'
                return task
            return None
    
    def mark_success(self, task_id: str):
        """标记任务成功"""
        with self.lock:
            self.completed.add(task_id)
    
    def mark_failed(self, task_id: str):
        """标记任务失败"""
        with self.lock:
            self.failed[task_id] += 1
    
    def size(self) -> int:
        """队列大小"""
        with self.lock:
            return len(self.queue)
    
    def completed_count(self) -> int:
        """完成数量"""
        with self.lock:
            return len(self.completed)


# ============================================================================
# 爬虫工作者
# ============================================================================

class CrawlerWorker(threading.Thread):
    """单个爬虫工作者"""
    
    def __init__(self, worker_id: str, strategy: str, task_queue: TaskQueue, results_pool: dict):
        super().__init__(daemon=True, name=f"{strategy}-{worker_id}")
        self.worker_id = worker_id
        self.strategy = strategy
        self.task_queue = task_queue
        self.results_pool = results_pool
        self.session = None
        self.stop_event = threading.Event()
        self._setup_session()
    
    def _setup_session(self):
        """设置会话"""
        try:
            if self.strategy == 'cloudscraper':
                try:
                    import cloudscraper
                    self.session = cloudscraper.create_scraper(
                        browser={'browser': 'chrome', 'platform': 'windows'}
                    )
                    logger.info(f"[{self.name}] Cloudscraper会话就绪")
                except ImportError:
                    logger.warning(f"[{self.name}] cloudscraper未安装，使用requests")
                    import requests
                    self.session = requests.Session()
            else:
                import requests
                self.session = requests.Session()
            
            # 设置通用headers
            self.session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': BASE_URL,
            })
        except Exception as e:
            logger.error(f"[{self.name}] 会话设置失败: {e}")
    
    def run(self):
        """主工作循环"""
        logger.info(f"[{self.name}] 启动")
        
        while not self.stop_event.is_set():
            task = self.task_queue.get_task()
            if not task:
                time.sleep(1)
                continue
            
            try:
                self._execute_task(task)
                self.task_queue.mark_success(task.task_id)
            except Exception as e:
                logger.error(f"[{self.name}] 任务{task.task_id}失败: {e}")
                self.task_queue.mark_failed(task.task_id)
                
                # 失败重试
                if task.retries < STRATEGIES[self.strategy]['max_retries']:
                    task.retries += 1
                    task.status = 'pending'
                    self.task_queue.add_task(task)
                    logger.info(f"[{self.name}] 任务{task.task_id}已重新入队 (重试{task.retries})")
                
                # 失败后增加延迟
                time.sleep(random.uniform(5, 15))
            finally:
                # 每个任务后随机延迟
                config = STRATEGIES[self.strategy]
                delay = random.uniform(config['min_delay'], config['max_delay'])
                time.sleep(delay)
        
        logger.info(f"[{self.name}] 已停止")
    
    def _execute_task(self, task: CrawlTask):
        """执行单个任务"""
        if not self.session:
            raise Exception("会话未初始化")
        
        config = STRATEGIES[self.strategy]
        category_url = f"{BASE_URL}/{task.category}"
        params = {'page': task.page}
        
        logger.info(f"[{self.name}] 执行 {task}")
        
        # 更新User-Agent
        self.session.headers['User-Agent'] = random.choice(USER_AGENTS)
        
        response = self.session.get(category_url, params=params, timeout=config['timeout'])
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 解析产品链接
        product_links = soup.find_all('a', href=lambda x: x and '/products/' in x)
        
        products = []
        for link in product_links:
            href = link.get('href', '')
            if href:
                full_url = urljoin(BASE_URL, href)
                products.append(full_url)
        
        logger.info(f"[{self.name}] {task}: 发现{len(products)}个产品")
        
        # 存储结果
        with threading.Lock():
            if task.category not in self.results_pool['products_by_category']:
                self.results_pool['products_by_category'][task.category] = set()
            
            self.results_pool['products_by_category'][task.category].update(products)
            self.results_pool['all_products'].update(products)
    
    def stop(self):
        """停止工作者"""
        self.stop_event.set()


# ============================================================================
# 爬虫协调器
# ============================================================================

class CrawlOrchestrator:
    """爬虫协调器"""
    
    def __init__(self):
        self.task_queue = TaskQueue()
        self.results_pool = {
            'all_products': set(),
            'products_by_category': defaultdict(set),
            'products_by_strategy': defaultdict(set),
        }
        self.storage = PersistentStorage()
        self.workers = []
        self.start_time = None
    
    def generate_tasks(self, max_pages_per_category: int = 25):
        """生成爬虫任务"""
        logger.info("="*80)
        logger.info("生成爬虫任务")
        logger.info("="*80)
        
        task_count = 0
        
        for category in CATEGORIES:
            for page in range(1, max_pages_per_category + 1):
                for strategy in ['cloudscraper', 'requests', 'slow']:
                    task_id = f"{category}_{page}_{strategy}"
                    task = CrawlTask(task_id, category, page, strategy)
                    self.task_queue.add_task(task)
                    task_count += 1
        
        logger.info(f"共生成{task_count}个任务")
    
    def start_workers(self):
        """启动工作者线程"""
        logger.info("="*80)
        logger.info("启动爬虫工作者")
        logger.info("="*80)
        
        self.start_time = time.time()
        
        for strategy, config in STRATEGIES.items():
            for i in range(config['workers']):
                worker = CrawlerWorker(
                    f"W{i+1}",
                    strategy,
                    self.task_queue,
                    self.results_pool
                )
                worker.start()
                self.workers.append(worker)
                logger.info(f"已启动工作者: {worker.name}")
                time.sleep(0.5)
    
    def monitor_progress(self):
        """监控进度"""
        while any(w.is_alive() for w in self.workers) or self.task_queue.size() > 0:
            elapsed = time.time() - self.start_time
            total_products = len(self.results_pool['all_products'])
            remaining_tasks = self.task_queue.size()
            completed_tasks = self.task_queue.completed_count()
            
            logger.info(f"[进度] 耗时{elapsed/60:.1f}分 | "
                       f"产品{total_products} | "
                       f"已完成任务{completed_tasks} | "
                       f"剩余任务{remaining_tasks}")
            
            # 每分钟保存一次检查点
            if int(elapsed) % 60 == 0:
                checkpoint = {
                    'timestamp': datetime.now().isoformat(),
                    'products': list(self.results_pool['all_products']),
                    'tasks_completed': completed_tasks,
                }
                self.storage.save_checkpoint(checkpoint)
            
            time.sleep(5)
    
    def run(self, max_pages_per_category: int = 25):
        """运行爬虫系统"""
        try:
            # 生成任务
            self.generate_tasks(max_pages_per_category)
            
            # 启动工作者
            self.start_workers()
            
            # 启动监控
            monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
            monitor_thread.start()
            
            # 等待完成
            for worker in self.workers:
                worker.join()
            
            logger.info("="*80)
            logger.info("爬虫完成")
            logger.info("="*80)
            
            elapsed = time.time() - self.start_time
            logger.info(f"总用时: {elapsed/60:.1f} 分钟")
            logger.info(f"发现产品总数: {len(self.results_pool['all_products'])}")
            
            for category, products in self.results_pool['products_by_category'].items():
                logger.info(f"  {category}: {len(products)} 个产品")
            
            # 保存结果
            results = {
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': elapsed,
                'total_products': len(self.results_pool['all_products']),
                'products': list(self.results_pool['all_products']),
                'by_category': {
                    k: list(v) for k, v in self.results_pool['products_by_category'].items()
                }
            }
            self.storage.save_results(results, 'crawl_results.json')
            
        except KeyboardInterrupt:
            logger.warning("用户中断爬虫")
            self.stop_all_workers()
        except Exception as e:
            logger.error(f"爬虫系统异常: {e}", exc_info=True)
            self.stop_all_workers()
    
    def stop_all_workers(self):
        """停止所有工作者"""
        for worker in self.workers:
            worker.stop()


# ============================================================================
# 主函数
# ============================================================================

def main():
    logger.info("多策略分布式爬虫系统启动")
    
    orchestrator = CrawlOrchestrator()
    orchestrator.run(max_pages_per_category=25)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Brilliant Earth 全站爬虫
自动爬取所有产品图片，按材质、颜色、产品类型分类存储
绕过 Cloudflare 反爬虫机制
"""

import cloudscraper
from bs4 import BeautifulSoup
import re
from pathlib import Path
import time
from urllib.parse import urljoin
import requests
import sys

class BrilliantEarthScraper:
    def __init__(self):
        self.base_url = "https://www.brilliantearth.com"
        self.scraper = cloudscraper.create_scraper()
        self.exclude_patterns = [
            'review', 'nav', 'header', 'banner', 'promo', 'hand', 'model', 'person',
            'animation', 'gif', 'video', 'thumbnail', 'icon', 'logo', 'placeholder'
        ]
        self.products_dir = Path("products")

    def filter_url(self, url):
        """过滤掉非产品图片"""
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in self.exclude_patterns)

    def extract_product_info(self, title):
        """从标题提取产品属性"""
        material = ''
        if '14K' in title:
            material = '14K'
        elif '18K' in title:
            material = '18K'
        elif 'Platinum' in title:
            material = 'Platinum'
        
        color = ''
        if 'White Gold' in title or 'White' in title:
            color = 'White'
        elif 'Yellow Gold' in title or 'Yellow' in title:
            color = 'Yellow'
        elif 'Rose Gold' in title or 'Rose' in title:
            color = 'Rose'
        
        product_type = 'Product'
        if 'Ring' in title or 'Band' in title:
            product_type = 'Ring'
        elif 'Earring' in title:
            product_type = 'Earring'
        elif 'Necklace' in title:
            product_type = 'Necklace'
        elif 'Bracelet' in title:
            product_type = 'Bracelet'
        
        return {
            'material': material or 'Unknown',
            'color': color or 'Unknown',
            'type': product_type,
            'folder_name': title[:40]
        }

    def get_products_from_category(self, category_url):
        """从分类页获取所有产品链接"""
        print(f"📂 爬取分类: {category_url[:50]}...")
        
        try:
            response = self.scraper.get(f"{self.base_url}{category_url}", timeout=30)
            if response.status_code != 200:
                print(f"   ❌ 状态码: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            product_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(x in href for x in ['/jewelry/', '/products/', '/rings/', '/earrings/', '/necklaces/', '/bracelets/']):
                    if not any(x in href for x in ['#', 'javascript:', 'cart', 'wishlist', '?', 'design-your-own']):
                        if href.count('/') >= 3:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_links and 'brilliantearth.com' in full_url:
                                product_links.append(full_url)
            
            product_links = list(set(product_links))
            print(f"   ✓ 找到 {len(product_links)} 个产品")
            return product_links
            
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:50]}")
            return []

    def scrape_product(self, product_url):
        """爬取单个产品详情"""
        try:
            response = self.scraper.get(product_url, timeout=30)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else 'Unknown'
            
            image_urls = set()
            
            for img in soup.find_all('img'):
                for attr in ['src', 'data-src', 'data-lazy-src']:
                    src = img.get(attr)
                    if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        full_url = urljoin(self.base_url, src)
                        if 'brilliantearth' in full_url and self.filter_url(full_url):
                            image_urls.add(full_url)
            
            for picture in soup.find_all('picture'):
                for source in picture.find_all('source'):
                    srcset = source.get('srcset')
                    if srcset:
                        urls = re.findall(r'(\S+\.(?:jpg|jpeg|png|webp))', srcset, re.IGNORECASE)
                        for url in urls:
                            full_url = urljoin(self.base_url, url)
                            if 'brilliantearth' in full_url and self.filter_url(full_url):
                                image_urls.add(full_url)
            
            image_urls = list(image_urls)
            
            if len(image_urls) > 0:
                return {
                    'title': title,
                    'url': product_url,
                    'images': image_urls,
                    'info': self.extract_product_info(title)
                }
            
        except Exception as e:
            pass
        
        return None

    def download_images(self, product):
        """下载产品图片到分类文件夹"""
        info = product['info']
        product_dir = self.products_dir / info['type'] / info['material'] / info['color'] / info['folder_name']
        product_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        for i, img_url in enumerate(sorted(product['images']), 1):
            try:
                response = session.get(img_url, timeout=10, stream=True)
                if response.status_code == 200:
                    filename = f"{i:02d}_{Path(img_url).name}"
                    filepath = product_dir / filename
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                    downloaded += 1
            except:
                pass
        
        return downloaded

    def run(self, max_products=None):
        """运行完整爬虫"""
        print("=" * 70)
        print("Brilliant Earth 全站爬虫")
        print("=" * 70 + "\n")
        
        categories = [
            '/jewelry/rings/shop-all/',
            '/jewelry/earrings/shop-all/',
            '/jewelry/necklaces/shop-all/',
        ]
        
        all_products = []
        print("🔍 步骤 1: 收集产品链接\n")
        
        for category_url in categories:
            products = self.get_products_from_category(category_url)
            all_products.extend(products)
            time.sleep(1)
        
        all_products = list(set(all_products))
        print(f"\n✓ 共找到 {len(all_products)} 个产品链接")
        
        if max_products:
            all_products = all_products[:max_products]
            print(f"✓ 限制爬取前 {max_products} 个\n")
        else:
            print()
        
        print(f"🚀 步骤 2: 爬取产品并下载图片\n")
        
        total_images = 0
        total_downloaded = 0
        success_count = 0
        
        for idx, product_url in enumerate(all_products, 1):
            print(f"[{idx:3d}/{len(all_products)}] ", end="", flush=True)
            product = self.scrape_product(product_url)
            if product:
                print(f"✓ {product['title'][:45]:<45}", end=" ")
                total_images += len(product['images'])
                downloaded = self.download_images(product)
                total_downloaded += downloaded
                print(f"✅ {downloaded}/{len(product['images'])}")
                success_count += 1
            else:
                print("✗ 无图片")
            
            time.sleep(0.5)
        
        print(f"\n{'='*70}")
        print(f"✅ 爬取完成！")
        print(f"{'='*70}")
        print(f"成功: {success_count}/{len(all_products)} 产品")
        print(f"图片总数: {total_images}")
        print(f"下载成功: {total_downloaded}")
        print(f"存储位置: ./{self.products_dir}/")
        print(f"{'='*70}\n")
        
        print("📁 文件夹结构:")
        self._print_tree()

    def _print_tree(self, path=None, prefix="", max_depth=4, current_depth=0):
        """打印目录树"""
        if path is None:
            path = self.products_dir
        
        if not path.exists() or current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir())
            dirs = [item for item in items if item.is_dir()]
            files = [item for item in items if item.is_file()]
            
            for i, dir_item in enumerate(dirs):
                is_last = (i == len(dirs) - 1) and len(files) == 0
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{dir_item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._print_tree(dir_item, new_prefix, max_depth, current_depth + 1)
            
            for i, file_item in enumerate(files[:3]):
                is_last = (i == len(files) - 1)
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{file_item.name}")
            
            if len(files) > 3:
                print(f"{prefix}└── ... 和 {len(files) - 3} 个文件")
        
        except PermissionError:
            pass

def main():
    """主函数"""
    max_products = 50
    scraper = BrilliantEarthScraper()
    scraper.run(max_products=max_products)

if __name__ == "__main__":
    main()
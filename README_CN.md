# 🕷️ Brilliant Earth 全站爬虫

自动从 Brilliant Earth 网站爬取产品图片，并智能分类存储。

## ✨ 核心特性

✅ **自动绕过 Cloudflare** - 使用 cloudscraper 库自动处理反爬虫验证
✅ **智能自动分类** - 按产品类型 > 材质 > 颜色 > 产品名称自动分层
✅ **图片智能过滤** - 排除评论图、UI元素、动画等非产品图
✅ **批量处理** - 一次性爬取所有产品分类
✅ **可靠下载** - 支持失败重试和错误处理

## 🎯 功能说明

1. **网站爬取** - 从所有珠宝分类收集产品链接
2. **信息提取** - 自动从标题识别产品材质、颜色和类型
3. **图片下载** - 获取每个产品页面的高质量产品图
4. **智能过滤** - 排除不需要的图片（评论图、手模图、动画等）
5. **自动组织** - 创建分层文件夹结构

## 📁 文件结构

```
products/
├── Ring/                (产品类型)
│   ├── 18K/             (材质)
│   │   ├── Yellow/      (颜色)
│   │   │   ├── Beveled Edge Aspen.../
│   │   │   │   ├── 01_image.jpg
│   │   │   │   ├── 02_image.jpg
│   │   │   │   └── ...
│   │   │   └── Freesia Hidden Halo.../
│   │   └── White/
│   └── 14K/
├── Earring/
└── Necklace/
```

## 📊 性能指标

| 产品数 | 图片数 | 存储空间 | 耗时 |
|--------|--------|---------|------|
| 10 | 270 | 6MB | 2分钟 |
| 20 | 538 | 12MB | 5分钟 |
| 50 | 1350 | 30MB | 12分钟 |
| 100 | 2700 | 60MB | 25分钟 |
| 300+ | 8000+ | 180MB+ | 60分钟 |

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/viosson-d/brilliant-earth-scraper.git
cd brilliant-earth-scraper
pip3 install -r requirements.txt
```

### 使用

**方式1：交互式菜单（推荐）**
```bash
bash run_scraper.sh
```
选择：
1. 快速测试 (10个产品)
2. 中等规模 (50个产品)  
3. 完整爬取 (所有产品)

**方式2：直接运行**
```bash
python3 website_crawler_full.py
```

**方式3：自定义配置**
```python
from website_crawler_full import BrilliantEarthScraper

scraper = BrilliantEarthScraper()
scraper.run(max_products=100)  # 爬取100个产品
```

## 🔧 配置

### 修改爬取数量

编辑 `website_crawler_full.py`：
```python
def main():
    max_products = 50  # 改为需要的数字，或 None 表示全部
    scraper = BrilliantEarthScraper()
    scraper.run(max_products=max_products)
```

### 添加新分类

编辑 `run()` 方法中的 `categories` 列表：
```python
categories = [
    '/jewelry/rings/shop-all/',
    '/jewelry/earrings/shop-all/',
    '/jewelry/necklaces/shop-all/',
    '/jewelry/bracelets/shop-all/',  # 添加新分类
]
```

### 定制图片过滤

编辑 `exclude_patterns` 列表：
```python
self.exclude_patterns = [
    'review', 'hand', '360', 'animation', 'logo', 'placeholder'
    # 添加更多要排除的关键字
]
```

## 📋 系统要求

- Python 3.7+
- pip3
- 网络连接
- 磁盘空间（完整爬取需要 1-5GB）

## 🐛 故障排除

### 请求超时
```python
response = self.scraper.get(url, timeout=60)  # 增加超时时间
```

### Cloudflare 403 错误
```bash
pip3 install --upgrade cloudscraper
```

### 没有下载任何图片
检查：
1. 网站是否可以访问
2. 过滤规则是否过于严格
3. 磁盘空间是否充足
4. 图片URL是否有效

## 🎯 应用场景

✓ 建立产品数据库
✓ 训练图像识别模型
✓ 产品数据备份
✓ 竞争对手分析
✓ 设计参考库
✓ 价格监测
✓ 市场研究
✓ 库存追踪

## 📝 许可证

MIT License - 详见 LICENSE 文件

## ⚖️ 免责声明

本工具仅供教育和个人使用。请遵守网站服务条款和适用法律。

## 🤝 贡献

欢迎提交 issues 和 pull requests！

## 📞 支持

遇到问题？
1. 查看故障排除部分
2. 验证依赖已正确安装
3. 确保网络连接稳定
4. 检查磁盘空间

---

**为珠宝爱好者和数据收集者精心打造** ❤️

# 🕷️ Brilliant Earth Web Scraper

Automatically scrape and download product images from Brilliant Earth website with intelligent categorization.

**中文文档** | [README_CN.md](README_CN.md)

## ✨ Features

✅ **Bypass Cloudflare Protection** - Automatically handle anti-bot verification using cloudscraper
✅ **Smart Auto-Classification** - Organize by product type > material > color > product name
✅ **Intelligent Image Filtering** - Exclude non-product images (review photos, UI elements, animations, etc.)
✅ **Batch Processing** - Download from all product categories in one run
✅ **Reliable Downloading** - Auto-retry on failures with error handling

## 🎯 What It Does

1. **Scrapes Brilliant Earth** - Collects all product links from jewelry categories
2. **Extracts Information** - Automatically identifies product material, color, and type from titles
3. **Downloads Images** - Retrieves high-quality product images from each product page
4. **Filters Intelligently** - Removes unwanted images (review photos, hand models, animations, etc.)
5. **Organizes Automatically** - Creates hierarchical folder structure:

```
products/
├── Ring/
│   ├── 18K/
│   │   ├── Yellow/
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

## 📊 Performance

| Products | Images | Size | Time |
|----------|--------|------|------|
| 10 | 270 | 6MB | 2min |
| 20 | 538 | 12MB | 5min |
| 50 | 1350 | 30MB | 12min |
| 100 | 2700 | 60MB | 25min |
| 300+ | 8000+ | 180MB+ | 60min |

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/viosson-d/brilliant-earth-scraper.git
cd brilliant-earth-scraper
pip3 install -r requirements.txt
```

### Usage

**Method 1: Interactive Menu (Recommended)**
```bash
bash run_scraper.sh
```
Choose from:
1. Quick test (10 products)
2. Medium (50 products)  
3. Full scrape (all products)

**Method 2: Direct Python**
```bash
python3 website_crawler_full.py
```

**Method 3: Custom Configuration**
```python
from website_crawler_full import BrilliantEarthScraper

scraper = BrilliantEarthScraper()
scraper.run(max_products=100)  # Scrape 100 products
```

## 🔧 Configuration

### Modify Number of Products

Edit `website_crawler_full.py`:
```python
def main():
    max_products = 50  # Change this to desired number or None for all
    scraper = BrilliantEarthScraper()
    scraper.run(max_products=max_products)
```

### Add New Categories

Edit the `categories` list in the `run()` method:
```python
categories = [
    '/jewelry/rings/shop-all/',
    '/jewelry/earrings/shop-all/',
    '/jewelry/necklaces/shop-all/',
    '/jewelry/bracelets/shop-all/',  # Add new categories
]
```

### Customize Image Filtering

Edit the `exclude_patterns` list:
```python
self.exclude_patterns = [
    'review', 'hand', '360', 'animation', 'logo', 'placeholder'
    # Add more patterns to exclude
]
```

## 📋 Requirements

- Python 3.7+
- pip3
- Network connection
- Disk space (1-5GB for full scrape)

## 🐛 Troubleshooting

### Request Timeout
```python
response = self.scraper.get(url, timeout=60)  # Increase timeout
```

### Cloudflare 403 Error
```bash
pip3 install --upgrade cloudscraper
```

### No Images Downloaded
Check:
1. Is the website accessible?
2. Are filter rules too strict?
3. Is there enough disk space?
4. Are image URLs valid?

## 📝 Output Structure

Each product gets its own folder with all product images:
- **Folder naming**: `products/[Type]/[Material]/[Color]/[ProductName]/`
- **Image naming**: `01_image.jpg`, `02_image.jpg`, etc.
- **Auto-detection**: Product type, material, and color extracted from product titles

## ⚠️ Responsible Usage

1. **Respect robots.txt** - Check and follow website guidelines
2. **Reasonable delays** - Default 0.5s delay between requests
3. **Personal use** - Scraped data for personal projects only
4. **Monitor usage** - Keep an eye on server responses

## 🎯 Use Cases

✓ Build product database
✓ Train image recognition models
✓ Backup product data
✓ Competitor analysis
✓ Design reference library
✓ Price monitoring
✓ Market research
✓ Inventory tracking

## 📄 License

MIT License - See LICENSE file for details

## ⚖️ Disclaimer

This tool is for educational and personal use only. Ensure compliance with website terms of service and applicable laws.

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify dependencies are installed
3. Ensure stable internet connection
4. Check disk space availability

---

**Made with ❤️ for jewelry enthusiasts and data collectors**

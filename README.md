# Yandex Images Crawler

[![PyPI - Version](https://img.shields.io/pypi/v/yandex-images-crawler?style=for-the-badge\&color=blue)](https://pypi.org/project/yandex-images-crawler/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/yandex-images-crawler?style=for-the-badge\&color=mediumpurple)](https://www.pepy.tech/projects/yandex-images-crawler)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yandex-images-crawler?style=for-the-badge)](https://pypi.python.org/pypi/yandex-images-crawler)
[![License](https://img.shields.io/github/license/suborofu/yandex-images-crawler?style=for-the-badge\&color=limegreen)](https://opensource.org/licenses/MIT)

---

## 📌 Description

**Yandex Images Crawler** allows you to automatically download images from Yandex Images.

Unlike many similar tools, it supports advanced filters such as:

* Image size
* Similar images
* Custom search parameters

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/robot00f/yandex-images-crawler.git
```

### 2. Navigate to the project directory

```bash
cd yandex-images-crawler
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the crawler using `download.py` and a Yandex Images link.

### ✔️ Basic example (Windows)

```bash
python yandex_images_crawler/download.py --links "YANDEX_LINK_HERE" --count 100 --dir "C:\Path\To\Your\Folder"
```

---

## 💻 Command examples

### ✔️ One-line (recommended for Windows)

```bash
python yandex_images_crawler/download.py --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" --count 50 --headless
```

### ✔️ Multi-line (Linux / macOS)

```bash
python yandex_images_crawler/download.py \
  --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" \
  --count 50 \
  --headless
```

---

## ⚙️ Parameters

* `--links` → Yandex Images URL (search or similar images)
* `--links-file` → File containing multiple links
* `--count` → Number of images to download
* `--dir` → Output directory
* `--prev-dir` → Skip already downloaded images
* `--size` → Minimum image size (e.g., `800x600`)
* `--loaders-per-link` → Parallel loaders (performance tuning)
* `--headless` → Run without opening a browser

---

## 💡 Advanced usage

### Download from "Similar Images" (imageview)

```bash
python yandex_images_crawler/download.py --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" --count 50 --headless
```

---

## 📖 Full CLI Reference

```bash
usage: yandex-images-crawler [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N]
                            [--dir DIR] [--prev-dir DIR] [--loaders-per-link N] [--headless]
```

| Option               | Description                      |
| -------------------- | -------------------------------- |
| `--links`            | Links to image search or preview |
| `--links-file`       | File with links (one per line)   |
| `--size`             | Minimum image size (WxH)         |
| `--count`            | Number of images to download     |
| `--dir`              | Output directory                 |
| `--prev-dir`         | Skip already downloaded images   |
| `--loaders-per-link` | Parallel downloads               |
| `--headless`         | Run without browser UI           |

---

## 🔗 How to get valid links

1. Go to [https://yandex.com/images](https://yandex.com/images)
2. Search for any image
3. Apply filters (size, color, type, etc.)
4. (Optional) Open "Similar Images"
5. Copy the URL from your browser

Example:

```
https://yandex.com/images/search?... 
```

---

## ⚠️ Notes

* Requires a compatible browser + driver (e.g., Chrome + ChromeDriver)
* Adjust paths depending on your OS
* Large downloads may take time depending on your connection

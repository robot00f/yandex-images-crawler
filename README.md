# Yandex Images Crawler

[![PyPI - Version](https://img.shields.io/pypi/v/yandex-images-crawler?style=for-the-badge&color=blue)](https://pypi.org/project/yandex-images-crawler/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/yandex-images-crawler?style=for-the-badge&color=mediumpurple)](https://www.pepy.tech/projects/yandex-images-crawler)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yandex-images-crawler?style=for-the-badge)](https://pypi.python.org/pypi/yandex-images-crawler)
[![GitHub License](https://img.shields.io/github/license/suborofu/yandex-images-crawler?style=for-the-badge&color=limegreen)](https://opensource.org/licenses/MIT)

## Description

`Yandex Images Crawler` allows you to download images from [Yandex Images](https://yandex.com/images) automatically.

Unlike most other projects, this package allows you to download images according to certain filters. For example, you can download images of a specified size or similar images.

## Installation

---

## 🚀 Installation & Usage

### 1. Clone the repository

```bash
git clone https://github.com/robot00f/yandex-images-crawler.git
```

### 2. Navigate to the project directory

```bash
cd yandex-images-crawler
```

### 3. Install dependencies

Make sure you have Python installed, then install the required packages:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the crawler

You can start the crawler by executing `download.py` and passing a Yandex Images link.

### Basic example

### ▶️ Command example

#### ✔️ One-line (recommended for Windows)

```bash
python yandex_images_crawler/download.py --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" --count 50 --headless
```

#### ✔️ Multi-line (Linux / macOS)

```bash
python yandex_images_crawler/download.py \
  --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" \
  --count 50 \
  --headless
```

---

### ⚙️ Extra

* `--headless` → runs the browser without opening a window (faster & cleaner for servers)

---

**Parameters:**

* `--links` → Yandex Images URL (search or similar images)
* `--count` → Number of images to download
* `--dir` → Output directory

---

## 💡 Advanced usage

### Download from "Similar Images" (imageview)

You can also use links from Yandex's **"Similar Images"** feature:

```bash
python yandex_images_crawler/download.py \
--links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" \
--count 50 \
 --headless
```

---

## ⚠️ Notes

* Make sure you have a compatible browser and driver installed (e.g., Chrome + ChromeDriver) if required by Selenium.
* Paths should be adjusted depending on your operating system.
* Large downloads may take time depending on your connection.

---


## Usage

```
usage: yandex-images-crawler [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N]
                             [--dir DIR] [--prev-dir DIR] [--loaders-per-link N] [--headless]

Yandex Images Crawler

options:
  -h, --help            show this help message and exit
  --links LINK1,...     Full links to image sets for download. Links should be separated by commas. Each     
                        link should lead to an image search result or to an open preview of an image. The    
                        program will open all links each in its own window.
  --links-file FILE     Text file with full links to image sets for download. Links should be separated by   
                        newlines. Each link should lead to an image search result or to an open preview of   
                        an image. The program will open all links each in its own window.
  --size WxH            Minimum size of images to download. Width an height should be separated by 'x'.      
  --count N             Required count of images to download. Do not set it at all for infinite count. A     
                        message appears if the desired number of images are downloaded.
  --dir DIR             Directory for new images.
  --prev-dir DIR        Directory of previously loaded images. Program skips the loading of already loaded   
                        images in another directory. Useful for re-downloading.
  --loaders-per-link N  Number of loaders per link. Use larger values to speed up loading, but take into     
                        account your computer's performance.
  --headless            Run the program in headless mode. The program will not open any browser windows.     
                        You can't fix some problems in browser windows manually, so use this option with     
                        caution.
```

### Links

To get correct links, follow the steps below:

1. Open [Yandex Images](https://yandex.com/images).
2. Search for images you need.
3. Set the search parameters:
   - Specify size, orientation, type or color.
   - Provide a site URL.
   - Find similar images.
4. Copy a link in the browser ([example](https://yandex.com/images/search?lr=10831&quality=95&rdrnd=531684&redircnt=1737888986.1&sign=304c88d47ac4545285d022ba151a7c35&text=rick%20roll%20meme&type=album)).

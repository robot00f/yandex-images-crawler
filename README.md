# Yandex Images Crawler

[![PyPI - Version](https://img.shields.io/pypi/v/yandex-images-crawler?style=for-the-badge&color=blue)](https://pypi.org/project/yandex-images-crawler/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/yandex-images-crawler?style=for-the-badge&color=mediumpurple)](https://www.pepy.tech/projects/yandex-images-crawler)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yandex-images-crawler?style=for-the-badge)](https://pypi.python.org/pypi/yandex-images-crawler)
[![License](https://img.shields.io/github/license/suborofu/yandex-images-crawler?style=for-the-badge&color=limegreen)](https://opensource.org/licenses/MIT)

---

## 📌 Description

**Yandex Images Crawler** allows you to automatically download full-resolution images from Yandex Images with minimal resource usage.

Key features:

* **Hybrid crawling engine (`--mode http | auto | browser`)**: runs pure HTTP by default with **no browser / no Selenium** (~50–60 MB RAM, single Python process), with optional automatic or manual fallback to Chrome.
* **Advanced Yandex filters**: download from search results, **Similar Images** (`cbir_page=similar`), custom sizes, colors, orientations, or specific domains.
* **SHA-256 deduplication**: skips duplicate images across runs (`--dir` and `--prev-dir`), compatible across HTTP and browser modes.

---

## ⚡ Crawling Modes (`--mode`)

| Mode | Browser / Selenium | RAM & CPU | Best for |
| --- | --- | --- | --- |
| `http` *(default)* | None | Minimal (1 process, threads) | Fast downloads with near-zero RAM/CPU usage |
| `auto` *(hybrid)* | Only if needed | Minimal unless fallback triggers | Starting lightweight via HTTP and automatically switching to Chrome if Yandex asks for CAPTCHA or stops paginating before `--count` |
| `browser` | Chrome + Selenium | Higher | Very large crawls or solving Yandex CAPTCHAs interactively (without `--headless`) |

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

Full hybrid install (HTTP + Selenium browser fallback):

```bash
pip install -r requirements.txt
```

HTTP-only minimal install (no Selenium needed):

```bash
pip install requests Pillow
```

---

## ▶️ Usage

Run the crawler using `download.py` and a Yandex Images link.

By default, it runs in **lightweight HTTP mode (`--mode http`)** without launching any browser.

### ✔️ Basic example — lightweight HTTP mode (default, Windows)

```bash
python yandex_images_crawler/download.py --links "YANDEX_LINK_HERE" --count 50 --dir "C:\Path\To\Your\Folder"
```

---

## 💻 Command examples

### ✔️ Ultra-lightweight HTTP mode (no browser, recommended)

```bash
python yandex_images_crawler/download.py --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" --count 50
```

### ✔️ Hybrid auto mode (HTTP first, fallback to browser if needed)

```bash
python yandex_images_crawler/download.py --links "YANDEX_LINK_HERE" --count 100 --mode auto
```

### ✔️ Browser mode (Selenium + Chrome)

```bash
python yandex_images_crawler/download.py --links "YANDEX_LINK_HERE" --count 100 --mode browser
```

### ✔️ Multi-line (Linux / macOS)

```bash
python yandex_images_crawler/download.py \
  --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" \
  --count 50 \
  --mode http
```

---

## ⚙️ Parameters

* `--links` → Yandex Images URL (search, preview, or similar images)
* `--links-file` → File containing multiple links (one per line)
* `--count` → Number of new images to download (omit for unlimited)
* `--dir` → Output directory (default: `yandex-images`)
* `--prev-dir` → Skip images already downloaded in another directory
* `--size` → Minimum image size in `WxH` format (e.g., `800x600`)
* `--loaders-per-link` → Parallel download workers per link
* `--mode` → Crawling mode: `http` (default, no browser), `auto` (hybrid), or `browser` (Selenium + Chrome)
* `--delay` → Delay in seconds between HTTP page requests (default: `1.0`)
* `--headless` → Run Chrome without UI (implies `--mode browser` if `--mode` is not set)

---

## 💡 Advanced usage

### Download high-res Similar Images skipping previous downloads (hybrid mode)

```bash
python yandex_images_crawler/download.py --links "https://yandex.ru/images/search?url=https%3A%2F%2Favatars.mds.yandex.net%2Fget-images-cbir%2F4541870%2FB7Mk2KGEiNXvtZo4o891ag148%2Forig&rpt=imageview&cbird=178&cbir_id=4541870%2FB7Mk2KGEiNXvtZo4o891ag148&cbir_page=similar" --size 1280x720 --count 100 --mode auto --delay 1.5 --dir "output" --prev-dir "old_output"
```

---

## 📖 Full CLI Reference

```bash
usage: yandex-images-crawler [-h] [--links LINK1,...] [--links-file FILE] [--size WxH] [--count N]
                             [--dir DIR] [--prev-dir DIR] [--loaders-per-link N]
                             [--mode {http,browser,auto}] [--delay SECONDS] [--headless]
```

| Option               | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| `--links`            | Links to image search or preview                            |
| `--links-file`       | File with links (one per line)                              |
| `--size`             | Minimum image size (`WxH`)                                  |
| `--count`            | Number of images to download                                |
| `--dir`              | Output directory                                            |
| `--prev-dir`         | Skip already downloaded images                              |
| `--loaders-per-link` | Parallel downloads                                          |
| `--mode`             | `http` (default, no browser), `auto` (hybrid), or `browser` |
| `--delay`            | Delay in seconds between HTTP page requests                 |
| `--headless`         | Run browser without UI (implies `--mode browser`)           |

---

## 🔗 How to get valid links

1. Go to [https://yandex.com/images](https://yandex.com/images)
2. Search for any image
3. Apply filters (size, color, type, etc.)
4. (Optional) Open "Similar Images"
5. Copy the URL from your browser

Example:

```text
https://yandex.com/images/search?...
```

---

## ⚠️ Notes

* Default `--mode http` does **not** launch Chrome or import Selenium (minimal RAM/CPU, requires only `requests` and `Pillow`).
* `--mode browser` and `--mode auto` fallback require Chrome + Selenium.
* If Yandex serves a SmartCaptcha during `--mode http`, the crawler stops cleanly and reports it; re-run with `--mode browser` (without `--headless`) to solve it manually in Chrome.
* Adjust paths depending on your OS.

import logging
import queue
import re
import time
from multiprocessing import Queue, Value, get_logger
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By


class YandexCrawler:
    def __init__(
        self,
        start_link: str,
        load_queue: Queue,
        id=0,
        headless_mode=False,
        is_active=Value("i", True),
    ):
        self.start_link: str = start_link
        self.load_queue: Queue = load_queue
        self.id: str = str(id)
        self.is_active = is_active

        # Configure Chrome WebDriver options
        driver_options = webdriver.ChromeOptions()
        driver_options.add_argument("--disable-blink-features=AutomationControlled")
        driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        driver_options.add_experimental_option("useAutomationExtension", False)
        driver_options.add_argument("--incognito")
        
        if headless_mode:
            driver_options.add_argument("--headless")
            
        self.driver = webdriver.Chrome(options=driver_options)
        
        # Mask WebDriver to avoid bot detection by Yandex
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Setup logging
        self.logger: logging.Logger = get_logger()
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def __get_image_link(self):
        width, height = None, None

        # Possible CSS classes containing image size info (grid redesign + legacy)
        size_sources = [
            "ImagesViewerGridSizeButton-Content",
            "ImagesViewerGridDownloadControl-Size",
            "ImagesViewerGridSizeButton-Button",
            "OpenImageButton-SizesButton",
            "MMViewerButtons-ImageSizes",
            "OpenImageButton-SaveSize",
            "Button2-Text",
        ]

        # Extract image dimensions
        for source in size_sources:
            if width is not None and height is not None:
                break
            for elem in self.driver.find_elements(By.CLASS_NAME, source):
                try:
                    match = re.search(r"(\d+)\s*[×xX]\s*(\d+)", elem.text or "")
                    if match:
                        width, height = int(match.group(1)), int(match.group(2))
                        break
                except Exception:
                    pass

        if width is None or height is None:
            self.logger.warning(
                f"Process #{self.id} can't get image size from DOM; loader will verify after download."
            )

        link = None

        # Possible CSS classes containing the high-res image URL (grid redesign + legacy)
        link_sources = [
            "ImagesViewerGridDownloadControl-Download",
            "OpenImageButton-Save",
            "MMViewerButtons-OpenImage",
            "MMViewerButtons-Button",
            "Button2_link",
            "Button2_view_default",
        ]

        # Ignore thumbnails or cached images
        blacklist = [
            "yandex-images",
            "avatars.mds.yandex.net",
        ]

        # Extract the source link of the image
        for source in link_sources:
            if link is not None:
                break
            for elem in self.driver.find_elements(By.CLASS_NAME, source):
                try:
                    href = elem.get_attribute("href")
                    if not href or not href.startswith("http"):
                        continue
                    for b in blacklist:
                        if b in href:
                            time.sleep(5)
                            href = elem.get_attribute("href")
                            break
                    if href and href.startswith("http"):
                        link = href
                        break
                except Exception:
                    pass

        # Fallback: extract img_url parameter from the viewer URL
        if link is None:
            try:
                img_urls = parse_qs(urlparse(self.driver.current_url).query).get(
                    "img_url"
                )
                if img_urls and img_urls[0].startswith("http"):
                    link = img_urls[0]
            except Exception:
                pass

        if link is None:
            self.logger.critical(f"Process #{self.id} can't get image link.")
            return

        while self.is_active.value:
            try:
                self.load_queue.put((link, (width, height)), timeout=1)
                break
            except queue.Full:
                continue

    def __open_first_preview(self):
        # If the URL already opens the image viewer directly, don't click a thumbnail
        next_selector = (
            "button[class*='ImagesViewer-ButtonNext'], "
            "button[class*='CircleButton_type_next'], "
            "button[class*='MediaViewer-ButtonNext'], "
            "[class*='ButtonNext']"
        )
        if self.driver.find_elements(By.CSS_SELECTOR, next_selector):
            return

        try:
            # Scroll down to force Yandex to load thumbnails (handles lazy loading)
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Process #{self.id} could not scroll: {e}")

        try:
            # Extensive list of Yandex selectors, including support for 'Similar Images' (imageview)
            selectors = ".serp-item__link, .CbirSimilarList-Thumb a, a.ImagesContentImage-Cover, img[class*='ImagesContentImage-Image_clickable']"
            
            # Find ALL matching image thumbnails on the page
            buttons = self.driver.find_elements(By.CSS_SELECTOR, selectors)
            
            if buttons:
                # Click the FIRST matching result using Javascript 
                # (This bypasses issues where invisible overlays block standard Selenium clicks)
                self.driver.execute_script("arguments[0].click();", buttons[0])
                time.sleep(4)
            else:
                self.logger.critical(f"Process #{self.id} found no thumbnails. Selectors failed.")
        except Exception as e:
            self.logger.critical(f"Process #{self.id} can't open the first image. Error: {e}")

    def __open_next_preview(self):
        try:
            # Find any button that navigates to the next image in the viewer
            btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button[class*='ImagesViewer-ButtonNext'], button[class*='CircleButton_type_next'], button[class*='MediaViewer-ButtonNext'], [class*='ButtonNext']",
            )
            # Click via JS to prevent overlay blocking issues
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except Exception:
            self.logger.critical(f"Process #{self.id} can't move to the next image.")

    def run(self):
        try:
            self.driver.get(self.start_link)

            # Wait for the page to fully load before interacting
            time.sleep(2)

            self.__open_first_preview()

            while True:
                if not self.is_active.value:
                    return

                try:
                    self.__get_image_link()
                    self.__open_next_preview()
                except Exception as e:
                    self.logger.critical(e)
                    time.sleep(10)
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

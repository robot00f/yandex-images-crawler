import logging
import time
from multiprocessing import Queue, Value, get_logger

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

        # Possible CSS classes containing image size info
        size_sources = [
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
                    width, height = [int(i) for i in elem.text.split("×")]
                    break
                except:
                    pass
        else:
            if width is None or height is None:
                self.logger.critical(f"Process #{self.id} can't get image size.")
                return

        link = None

        # Possible CSS classes containing the high-res image URL
        link_sources = [
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
                    link = elem.get_attribute("href")
                    for b in blacklist:
                        if b in link:
                            time.sleep(5)
                            link = elem.get_attribute("href")
                            break
                    break
                except:
                    pass
        else:
            if link is None:
                self.logger.critical(f"Process #{self.id} can't get image link.")
                return

        self.load_queue.put((link, (width, height)))

    def __open_first_preview(self):
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
                By.CSS_SELECTOR, "button[class*='CircleButton_type_next'], button[class*='MediaViewer-ButtonNext'], [class*='ButtonNext']"
            )
            # Click via JS to prevent overlay blocking issues
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
        except:
            self.logger.critical(f"Process #{self.id} can't move to the next image.")

    def run(self):
        self.driver.get(self.start_link)
        
        # Wait for the page to fully load before interacting
        time.sleep(2) 

        self.__open_first_preview()

        while True:
            if not self.is_active.value:
                self.driver.close()
                return

            try:
                self.__get_image_link()
                self.__open_next_preview()
            except Exception as e:
                self.logger.critical(e)
                time.sleep(10)

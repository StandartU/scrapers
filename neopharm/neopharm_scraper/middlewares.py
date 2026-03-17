import json
import os
import platform
from urllib.parse import parse_qs

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy import signals, Request, Spider


def get_current_chrome_version() -> int:
    if platform.system() == "Linux":
        res = os.popen("google-chrome --version").read()
        return int(res.split(" ")[2].split(".")[0])
    elif platform.system() == "Windows":
        res = os.popen(
            'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
        ).read()
        return int(res.split("REG_SZ")[1].strip().split(".")[0])


class SeleniumMiddleware:
    def __init__(self):
        options = uc.ChromeOptions()

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = uc.Chrome(
            options=options,
            version_main=get_current_chrome_version()
        )

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request: Request, spider: Spider):
        if not request.meta.get("selenium"):
            return None

        self.driver.get(request.url)

        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".item-card"))
        )

        selenium_cookies = {
            cookie['name']: cookie['value']
            for cookie in self.driver.get_cookies()
        }
        request.cookies = selenium_cookies

        user_agent = self.driver.execute_script("return navigator.userAgent;")

        request.headers.update({"User-Agent": user_agent})

        self.driver.quit()

        return None

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

    def spider_closed(self, spider):
        spider.logger.info("Spider closed: %s" % spider.name)

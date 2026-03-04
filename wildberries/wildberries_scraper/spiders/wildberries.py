from typing import AsyncIterator, Any

from scrapy import Spider, Request
from urllib.parse import urlencode

class WildberriesSpider(Spider):
    name = "wildberries_spider"
    allowed_domains = ["wildberries.ru"]

    def start(self) -> AsyncIterator[Any]:
        search_query = getattr(self, "search_query", None)

        if not search_query:
            raise ValueError('Use "scrapy crawl -a search_query=SEARCH_QUERY"')

        params = {"search": search_query}
        url = "https://www.wildberries.ru/catalog/0/search.aspx?" + urlencode(params)

        yield Request(url, callback=self.parse)

    def parse(self, **kwargs):
        pass

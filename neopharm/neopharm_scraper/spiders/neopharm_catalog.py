from scrapy import Spider, Request
from scrapy.http import HtmlResponse

from ..items import NeopharmScraperItemCatalog


class NeopharmSpider(Spider):
    name = "neopharm_spider"
    allowed_domains = [
        "neopharm.ru",
    ]

    # Айди города москва
    MOSCOW_CITY_ID = "1"

    async def start(self):
        yield Request(
            url="https://neopharm.ru/catalog",
            meta={"selenium": True},
            callback=self.get_pages
        )

    def get_pages(self, response: HtmlResponse):
        response.request.cookies.update({"cityId": self.MOSCOW_CITY_ID})

        self.logger.info(response.text)

        next_page = response.xpath('//div[contains(@class,"pagi-btn -next")][1]/a/@href').get()

        self.logger.info(next_page)

        if next_page:
            yield response.follow(next_page, callback=self.parse_item)

    def parse_item(self, response: HtmlResponse):
        if response.status == 500:
            return

        cards = response.xpath('//*[@id="catalog-drugs-block"]//div[contains(@class,"item-card")]')

        for card in cards:
            name = card.xpath('.//div[@class="text text-min-height mobile-max-width"]/text()').get()
            price = card.xpath('.//div[@class="new_price"]/span/text()').get()

            yield NeopharmScraperItemCatalog(
                name=name,
                price=price
            )

        next_page = response.xpath('//div[contains(@class,"pagi-btn -next")]//a/@href').get()

        if next_page:
            yield response.follow(next_page, callback=self.parse_item)

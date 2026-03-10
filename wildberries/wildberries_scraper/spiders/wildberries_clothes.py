from requests import Response
from scrapy import Spider, Request
from urllib.parse import urlencode, parse_qs

from scrapy.http import HtmlResponse


class WildberriesSpider(Spider):
    name = "wildberries_spider"
    allowed_domains = ["wildberries.ru"]
    # количество товаров в ответе вб
    SEARCH_PAGE_SIZE = 100

    async def start(self):
        search_query = getattr(self, "search_query", None)

        if not search_query:
            raise ValueError('Use "scrapy crawl NAME_SPIDER -a search_query=SEARCH_QUERY"\n'
                             'По условию задания: scrapy crawl wildberries_spider -a search_query="пальто из натуральной шерсти"')

        params = {"search": search_query}
        url = "https://www.wildberries.ru/catalog/0/search.aspx?" + urlencode(params)

        yield Request(
            url,
            callback=self.parse_products,
            meta={
                "selenium": True,
            },
        )


    def parse_products(self, response: HtmlResponse, page:int = None):
        search_query = getattr(self, "search_query", None)

        if page is None:
            page = 1

        params = {
            "query": search_query,
            "resultset": "catalog",
            "page": page,
            "lang": "ru",
            "sort": "popular",
            "suppressSpellcheck": "false"
        }

        geo_params = response.meta["geo_params"]

        params.update(geo_params)

        url = "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?" + urlencode(params)

        yield Request(
            url,
            callback=self.parse_details,
            meta={
                "search_params": params,
                "geo_params": geo_params
            },
            cookies=response.request.cookies,
        )

    def parse_details(self, response: HtmlResponse):
        search_data = response.json()

        if not len(search_data["products"]) < self.SEARCH_PAGE_SIZE:
            params = response.meta["search_params"]
            page = params.get("page") + 1
            params["page"] = page

            url = "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?" + urlencode(params)

            yield Request(
                url,
                callback=self.parse_details,
                meta=response.meta,
                cookies=response.request.cookies
            )

        url_details = "https://www.wildberries.ru/__internal/u-card/cards/v4/detail?"

        params = {
            "lang": "ru"
        }

        geo_params = response.meta["geo_params"]
        params.update(geo_params)

        products = search_data["products"]
        products_id = [p["id"] for p in products]

        nm_param = ";".join(map(str, products_id))
        params.update({"nm": nm_param})

        url = url_details + urlencode(params)

        yield Request(
            url,
            callback=self.process_items,
            cookies=response.request.cookies
        )

    def process_items(self, response: HtmlResponse):
        pass

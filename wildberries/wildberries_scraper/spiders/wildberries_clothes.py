from urllib.parse import urlencode
import json
import requests

from scrapy.http import HtmlResponse
from scrapy import Spider, Request

from ..items import WildberriesClothItem


class WBRouteMap:
    def __init__(self, url="https://cdn.wbbasket.ru/api/v3/upstreams"):
        self.url = url
        self.data = self.load_upstreams()

    def load_upstreams(self):
        import time
        r = requests.get(f"{self.url}?t={int(time.time()*1000)}")
        r.raise_for_status()
        return r.json()

    def get_basket_host(self, vol):
        hosts = self.data["recommend"]["mediabasket_route_map"][0]['hosts']
        for h in hosts:
            if h["vol_range_from"] <= vol <= h["vol_range_to"]:
                return h["host"]
        return None

class WildberriesSpider(Spider):
    name = "wildberries_spider"
    allowed_domains = [
        "wildberries.ru",
        "wbbasket.ru"
    ]

    # cdn сервера
    route_map = WBRouteMap()
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
                "geo_params": geo_params,
            },
            cookies=response.request.cookies,
            headers={
                "deviceid": response.meta["device_id"],
                "TE": "trailers",
                "User-Agent": response.meta["user_agent"],
                "x-requested-with": "XMLHttpRequest",
                "x-spa-version": "14.0.8"
            }
        )

    def parse_details(self, response: HtmlResponse):
        search_data = response.json()

        if "products" not in search_data:
            self.logger.error(f"'products' not in {response.url}, retry...")
            yield response.request.replace(dont_filter=True)
            return

        if len(search_data["products"]) == self.SEARCH_PAGE_SIZE:
            params = response.meta["search_params"]
            page = params.get("page") + 1
            params["page"] = page

            url = "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?" + urlencode(params)

            yield Request(
                url,
                callback=self.parse_details,
                meta=response.meta,
                cookies=response.request.cookies,
                headers=response.request.headers
            )
        else:
            self.logger.info("COMPLETED AT PAGE: " + str(response.meta["search_params"].get("page")))

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
            cookies=response.request.cookies,
            headers=response.request.headers
        )

    def process_items(self, response: HtmlResponse):

        data = response.json()

        for product in data.get("products", []):

            product_id = product["id"]

            url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"

            name = product.get("name")

            price = None
            for size in product.get("sizes", []):
                try:
                    price = size["price"]["product"] / 100
                    break
                except KeyError:
                    continue

            if price is None:
                self.logger.exception(f"MISS ITEM {product['id']} — нет доступной цены")

            seller_name = product.get("supplier")

            seller_url = f"https://www.wildberries.ru/seller/{product['supplierId']}"

            rating = product.get("reviewRating")

            reviews = product.get("feedbacks")

            quantity = product.get("totalQuantity")

            sizes = ",".join([s["name"] for s in product["sizes"]])

            pics_count = product["pics"]

            vol = product_id // 100000
            part = product_id // 1000

            images = []

            basket_host = self.route_map.get_basket_host(vol)

            for i in range(1, pics_count + 1):
                img = f"https://{basket_host}/vol{vol}/part{part}/{product_id}/images/big/{i}.webp"
                images.append(img)

            images = ",".join(images)

            item = {
                "url": url,
                "article": product_id,
                "name": name,
                "price": price,
                "description": None,
                "images": images,
                "seller": seller_name,
                "seller_url": seller_url,
                "sizes": sizes,
                "quantity": quantity,
                "rating": rating,
                "reviews": reviews,
            }

            card_url = f"https://{basket_host}/vol{vol}/part{part}/{product_id}/info/ru/card.json"

            yield Request(
                card_url,
                callback=self.parse_description,
                meta={"item": item},
                cookies=response.request.cookies,
                headers=response.request.headers
            )

    def parse_description(self, response):
        item_dict = response.meta["item"]
        data = response.json()

        item_dict["description"] = data.get("description")

        characteristics = [
            {"name": opt.get("name"), "value": opt.get("value")}
            for opt in data.get("options", [])
        ]
        characteristics_json = json.dumps(characteristics)
        item_dict["characteristics"] = characteristics_json

        yield WildberriesClothItem(**item_dict)
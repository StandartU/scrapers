# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class WildberriesClothItem(scrapy.Item):
    url = scrapy.Field()
    article = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    characteristics = scrapy.Field()
    images = scrapy.Field()
    seller = scrapy.Field()
    seller_url = scrapy.Field()
    sizes = scrapy.Field()
    quantity = scrapy.Field()
    rating = scrapy.Field()
    reviews = scrapy.Field()

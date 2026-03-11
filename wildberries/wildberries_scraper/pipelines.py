# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import json
import sqlite3

import pandas as pd



class SQLiteWbClothPipeline:

    def open_spider(self, spider):
        self.conn = sqlite3.connect("wb_products.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                article INTEGER PRIMARY KEY,
                url TEXT,
                name TEXT,
                price REAL,
                description TEXT,
                characteristics TEXT,
                images TEXT,
                seller TEXT,
                seller_url TEXT,
                sizes TEXT,
                quantity INTEGER,
                rating REAL,
                reviews INTEGER
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        self.conn.commit()
        self.conn.close()
        self.export_to_excel()

    def process_item(self, item, spider):

        self.cursor.execute("""
            INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            item.get("article"),
            item.get("url"),
            item.get("name"),
            item.get("price"),
            item.get("description"),
            item.get("characteristics"),
            item.get("images"),
            item.get("seller"),
            item.get("seller_url"),
            item.get("sizes"),
            item.get("quantity"),
            item.get("rating"),
            item.get("reviews"),
        ))
        return item

    def export_to_excel(self):
        conn = sqlite3.connect("wb_products.db")
        df = pd.read_sql("SELECT * FROM products", conn)
        # распарсим характеристики в текст для Excel
        def char_to_text(json_str):
            try:
                return "; ".join([f"{c['name']}: {c['value']}" for c in json.loads(json_str)])
            except:
                return ""
        df["characteristics"] = df["characteristics"].apply(char_to_text)
        df.to_excel("results/wb_catalog.xlsx", index=False)
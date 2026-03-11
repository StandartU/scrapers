import sqlite3
from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "wb_products.db"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM products", conn)

def is_made_in_russia(characteristics_json):
    try:
        characteristics = json.loads(characteristics_json) if characteristics_json else []
        return any(
            c.get("name", "").lower() == "страна производства" and c.get("value") == "Россия"
            for c in characteristics
        )
    except json.JSONDecodeError:
        return False

filtered = df[
    (df["rating"] >= 4.5) &
    (df["price"] <= 10000) &
    (df["characteristics"].apply(is_made_in_russia))
]

filtered.to_excel(BASE_DIR / "results/filtered_wb.xlsx", index=False)
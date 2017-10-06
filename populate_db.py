"""Script to populate db."""
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_csv("input.csv")
df["verified"] = 0
db = create_engine("sqlite:///OSM_Tamil_translation_TN.db", echo=False)
df.to_sql(
    "translation",
    db,
    if_exists="append",
    index=False,
    index_label='OSM_ID')

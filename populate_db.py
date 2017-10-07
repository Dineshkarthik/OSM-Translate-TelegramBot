"""Script to populate db."""
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(THIS_DIR, 'config.yaml'))
config = yaml.safe_load(f)
f.close()


df = pd.read_csv(config["input_csv"])
df["verified"] = 0
db = create_engine("sqlite:///" + config["db_name"] + ".db", echo=False)
df.to_sql("translation", db, if_exists="append")

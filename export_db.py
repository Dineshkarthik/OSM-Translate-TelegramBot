"""Script to export DB to csv."""
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(THIS_DIR, 'config.yaml'))
config = yaml.safe_load(f)
f.close()

db = create_engine(
    "sqlite:///" + config["db_name"] + ".db?check_same_thread=False",
    echo=False)

df = pd.read_sql_table('translation', db)
df.to_csv(config["db_name"] + ".csv", index=False)

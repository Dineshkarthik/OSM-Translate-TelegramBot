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
    'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(
        config['db_username'], config['db_password'], config['db_host'],
        config['db_port'], config['db_name']),
    encoding='utf-8',
    echo=False)

df = pd.read_sql_table('translation', db)
df = df[(df["translator_id"] != 0) | (df["verified"] == 3)]
df.to_csv(config["db_name"] + ".csv", index=False)

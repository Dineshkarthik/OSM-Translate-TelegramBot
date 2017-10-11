"""Script to populate db."""
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(THIS_DIR, 'config.yaml'))
config = yaml.safe_load(f)
f.close()

database = config['db_name']
mysql_engine = create_engine('mysql+mysqldb://{0}:{1}@{2}:{3}'.format(config[
    'db_username'], config['db_password'], config['db_host'], config[
        'db_port']))

existing_databases = mysql_engine.execute("SHOW DATABASES;")
existing_databases = [d[0] for d in existing_databases]

if database not in existing_databases:
    mysql_engine.execute(
        "CREATE DATABASE {0} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".
        format(database))
    print("Created database {0}".format(database))

db = create_engine(
    'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format(
        config['db_username'], config['db_password'], config['db_host'],
        config['db_port'], database),
    encoding='utf-8',
    echo=False)

df = pd.read_csv(config["input_csv"])
df["verified"] = 0
df.index = df.index + 1
df.loc[df.name == df.translation, 'translation'] = None
df.to_sql("translation", db, if_exists="append")
print("Created table translation")

user_df = pd.DataFrame(columns=[
    'user_id', 'osm_username', 'tlg_username', 'first_name', 'last_name',
    'translate', 'verify', 'verify_count'
])
user_df.to_sql("users", db, if_exists="fail", index=False)
print("Created table users")

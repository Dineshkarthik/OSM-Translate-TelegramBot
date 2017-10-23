"""Script to populate db."""
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, types

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

existing_tables = db.execute("SHOW TABLES;")
existing_tables = [d[0] for d in existing_tables]

df = pd.read_csv(config["input_csv"], sep="~")
df["verified"] = 0
df.index = df.index + 1
df["translator_id"] = 0
df["is_exported"] = 0
df.loc[df.name == df.translation, 'translation'] = None

if 'translation' in existing_tables:
    max_index = pd.read_sql_query('select max(`index`) from translation',
                                  db).max()
    df.index = df.index + max_index[0]
    print("Updating table translation")
else:
    print("Creating table translation")
df.to_sql(
    "translation",
    db,
    if_exists="append",
    dtype={'translation': types.VARCHAR(250)})

if 'translation' not in existing_tables:
    indexes = [
        "CREATE UNIQUE INDEX ix_osm_id on translation (osm_id);",
        "CREATE INDEX ix_get_verified on translation (`index`, verified, translation);",
        "CREATE INDEX ix_get_translation on translation (`index`, verified, translator_id);"
    ]
    for index in indexes:
        db.execute(index)

if 'users' not in existing_tables:
    user_df = pd.DataFrame(columns=[
        'user_id', 'osm_username', 'tlg_username', 'first_name', 'last_name',
        'translate', 'verify', 'translate_count', 'verify_count', 't_index',
        'v_index'
    ])
    int_columns = [
        "user_id", "translate", "verify", "translate_count", "verify_count",
        "t_index", "v_index"
    ]
    user_df[int_columns] = user_df[int_columns].astype(int)
    user_df.to_sql(
        "users", db, if_exists="fail", index=False, index_label='user_id')
    db.execute("CREATE INDEX ix_user_id on users (user_id);")
    print("Created table users")

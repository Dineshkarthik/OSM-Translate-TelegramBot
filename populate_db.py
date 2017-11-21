"""Script to populate db."""
import os
import yaml
import pandas as pd
from sqlalchemy import create_engine, types, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

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
Base = declarative_base()
Base.metadata.reflect(db)
Session = sessionmaker(bind=db)
session = Session()

existing_tables = db.execute("SHOW TABLES;")
existing_tables = [d[0] for d in existing_tables]


def import_data():
    """Import data to db."""
    df = pd.read_csv(config["input_csv"], sep="~")
    df["verified"] = 0
    df.index = df.index + 1
    df["translator_id"] = 0
    df["is_exported"] = 0
    df.loc[df.name == df.translation, 'translation'] = None

    if 'translation' in existing_tables:

        class Data(Base):
            """Class for translation table."""

            __table__ = Base.metadata.tables['translation']
            __mapper_args__ = {'primary_key': [__table__.c.osm_id]}

        def check_exists(row):
            """Check if a entry exists in db."""
            r = session.query(Data).filter(
                Data.name == row["name"],
                or_(Data.verified == 3, Data.translator_id != 0)).first()
            if r:
                row["translation"] = r.translation
                row["verified"] = 3
            return row

        max_index = pd.read_sql_query('select max(`index`) from translation',
                                      db).max()
        df.index = df.index + max_index[0]
        print("Updating table translation")
        df = df.apply(check_exists, axis=1)
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
            'user_id', 'osm_username', 'tlg_username', 'first_name',
            'last_name', 'translate', 'verify', 'translate_count',
            'verify_count', 't_index', 'v_index', 'is_admin'
        ])
        int_columns = [
            "user_id", "translate", "verify", "translate_count",
            "verify_count", "t_index", "v_index", "is_admin"
        ]
        user_df[int_columns] = user_df[int_columns].astype(int)
        user_df.to_sql(
            "users", db, if_exists="fail", index=False, index_label='user_id')
        db.execute("CREATE INDEX ix_user_id on users (user_id);")
        print("Created table users")


def add_admin():
    """Function to update admin roles."""
    for admin in config["bot_admin"]:
        query = "UPDATE `users` SET `is_admin`='1' WHERE `tlg_username`='" + admin + "';"
        db.execute(query)
    print("Admin roles updated...!")


if __name__ == "__main__":
    import_data()
    add_admin()

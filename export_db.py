"""Script to export DB to csv."""
import os
import yaml
import pandas as pd
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *

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

Base = declarative_base()
Base.metadata.reflect(db)
Session = sessionmaker(bind=db)
session = Session()
filename = config["db_name"] + ".csv"


class Data(Base):
    """Class for translation table."""

    __table__ = Base.metadata.tables['translation']
    __mapper_args__ = {'primary_key': [__table__.c.osm_id]}


df = pd.read_sql_table('translation', db)

if config["export_type"] == "batch":
    df = df[((df["translator_id"] != 0) | (df["verified"] == 3)) & (df[
        "is_exported"] == 0)]
else:
    df = df[(df["translator_id"] != 0) | (df["verified"] == 3)]

if len(df) != 0:
    df.to_csv(filename, index=False, sep="~")
    print("%s - Export Completed...\nUpdating export status in DB..." %
          filename)

    _ids = tuple(df.osm_id.tolist())
    session.query(Data).filter(Data.osm_id.in_(_ids)).update(
        {
            Data.is_exported: 1
        }, synchronize_session=False)
    session.commit()
else:
    print("No new data available to export...!")

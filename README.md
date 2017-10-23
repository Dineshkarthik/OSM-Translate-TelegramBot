# **OSM-Translate-TelegramBot**

This bot it designed to help translation of [OpenStreetMap](https://www.openstreetmap.org) location from English to any Regional Language.

## Tech

OSM-Translate-TelegramBot uses various python packages / open source projects to work properly:

* [Pandas] - pandas is an open source, library providing high-performance, easy-to-use data structures and data analysis tools for the Python.
* [SQLAlchemy] -  Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
* [pyTelegramBotAPI] - A simple, but extensible Python implementation for the [Telegram Bot API](https://core.telegram.org/bots/api).
* [PyYAML] - YAML parser and emitter for Python.
* [MySQL] - Database being used.


## Installation

Tested on python 3.* 
```sh
$ git clone https://github.com/Dineshkarthik/OSM-Translate-TelegramBot.git
$ cd OSM-Translate-TelegramBot
$ pip install -r requirements.txt
```

## Configuration 

     token: 'YOUR_BOT_TOKEN'
     input_csv: '/PATH/TO/YOUR/INPUT/INPUT.CSV'
     db_name: 'NAME_FOR_DB_TO_BE_GENERATED'
     db_username: 'MYSQL_USER_NAME'
     db_password: 'MYSQL_PASSWORD'
     db_host: 'localhost'
     db_port: 3306
     

 - token  - Your Telegram Bot API Token, to get the token follow the instructions available [here](https://core.telegram.org/bots#6-botfather)
 - input_csv - Path to the input csv file, which contains the Locations to be translated.
  - The Input csv file should consists of the following `3 mandatory columns`
    - osm_id - OSM Node ID of the Location
    - name - Name of the Location to be translated
    - translation - Suggested Google or any other translation if available (But the column is mandatory)
 - db_name -  Name of the MySQL db, will be generated if not exists.
 - db_username - User name to connect to MySQL database.
 - db_password - Password to connect to DB.
 - db_host - Hostname of the DB, if using local database use `localhost`
 - db_port - Port to connect to db, MySQL default port is 3306
 - export_type - For exporting data from DB
    - batch - To export data which is not exported already.
    - all - To export all available data which are wither verified or translated.

## Execution
```sh
$ python populated_db.py 
$ python translate_bot.py
$ python export_db.py
```
* Running `populated_db.py` will generate a MySQL DB if not already created and will seed it with data from the input csv file.
* Running `translate_bot.py` will start the Telegram Bot.  
* Runnign `export_db.py` will export translated data available in DB to a CSV file.

   [Pandas]: <http://pandas.pydata.org/>
   [SQLAlchemy]: <https://www.sqlalchemy.org/>
   [pyTelegramBotAPI]: <https://github.com/eternnoir/pyTelegramBotAPI>
   [PyYAML]: <https://pypi.python.org/pypi/PyYAML>
   [MySQL]: <https://www.mysql.com/>
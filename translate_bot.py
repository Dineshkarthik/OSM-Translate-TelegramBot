"""TelegramBot for OSM translation."""
import os
import yaml
import telebot
from telebot import types
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(THIS_DIR, 'config.yaml'))
config = yaml.safe_load(f)
f.close()

bot = telebot.TeleBot(config["token"])
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

_dict = {}


class Data(Base):
    """Class for translation table."""

    __table__ = Base.metadata.tables['translation']
    __mapper_args__ = {'primary_key': [__table__.c.osm_id]}


class User(Base):
    """Class for user table."""

    __table__ = Base.metadata.tables['users']
    __mapper_args__ = {'primary_key': [__table__.c.user_id]}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """/start."""
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    if not session.query(exists().where(User.user_id == user_id)).scalar():
        msg = bot.send_message(message.chat.id, """\
Dear """ + user_name + """, We appreciate your interest in contributing to OSM.

We keep track of all your contributions, hence need your OSM username,
Please reply with your OSM username.

If you don't have one, Plesae use the following link and create one
https://www.openstreetmap.org/user/new
""")
        bot.register_next_step_handler(msg, create_user_entry)
    else:
        user = session.query(User).filter_by(user_id=user_id).first()
        bot.send_message(
            message.chat.id, """\
Dear """ + user.first_name +
            """, We appreciate your interest in contributing to OSM.
Your OSM username is """ + user.osm_username + """

Incase you want to update your OSM username use - /updateusername

Use /contribute to start contributing
""")


def create_user_entry(message):
    """Creating user entry in users table."""
    user = User()
    user.first_name = message.from_user.first_name
    user.last_name = message.from_user.last_name
    user.osm_username = message.text
    user.tlg_username = message.from_user.username
    user.user_id = message.from_user.id
    user.verify_count = 0
    user.t_index = 0
    session.add(user)
    session.commit()
    bot.send_message(
        message.chat.id,
        """\
Your OSM username *""" + message.text + """* is successfully updated.

Incase you want to update your OSM username use - /updateusername

Use /contribute to start contributing
""",
        parse_mode='markdown')


@bot.message_handler(commands=['updateusername'])
def update_user(message):
    """/updateusername."""
    msg = bot.send_message(
        message.chat.id,
        "Please reply with the new OSM username you wish to update.")
    bot.register_next_step_handler(msg, update_username)


def update_username(message):
    """Update OSM username."""
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    user.osm_username = message.text
    session.commit()
    bot.send_message(
        message.chat.id,
        """\
Your OSM username *""" + message.text + """* is successfully updated.

Use /contribute to start contributing
""",
        parse_mode='markdown')


@bot.message_handler(commands=['contribute', 'help'])
def send_instructions(message):
    """/contribute."""
    bot.send_message(message.chat.id, """\
I can help you translate contents to Tamil seamlessly.

You can control me by sending these commands:

/translate - To start translating.
/verify - To verify translations.""")


@bot.message_handler(commands=['verify'])
def get_verified(message):
    """/verify."""
    chat_id = message.chat.id
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    bot.send_chat_action(chat_id, 'typing')
    result = session.query(Data).filter(Data.verified < 3,
                                        Data.index > user.t_index,
                                        Data.translation != None).first()
    text = "Is *%s* a correct translation of *%s*" % (result.translation,
                                                      result.name)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Correct', 'Wrong')
    user.verify = result.osm_id
    user.t_index = result.index
    session.commit()
    msg = bot.send_message(
        chat_id, text, reply_markup=markup, parse_mode='markdown')
    bot.register_next_step_handler(msg, commit_verify)


def commit_verify(message):
    """Commit to DB."""
    if message.text.lower() != '/translate':
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        if message.text == 'Correct':
            row = session.query(Data).filter_by(osm_id=user.verify).first()
            row.verified += 1
            user.verify_count += 1
            session.commit()
        elif message.text == 'Wrong':
            row = session.query(Data).filter_by(osm_id=user.verify).first()
            row.verified -= 1 if row.verified != 0 else 0
            user.verify_count += 1
            session.commit()
        get_verified(message)


@bot.message_handler(commands=['translate'])
def get_translate(message):
    """/translate."""
    chat_id = message.chat.id
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    bot.send_chat_action(chat_id, 'typing')
    result = session.query(Data).filter(Data.verified == 0,
                                        Data.index > user.t_index).first()
    text = "Translation for *%s*\nIf not sure please reply /skip" % result.name
    user.translate = result.osm_id
    user.t_index = result.index
    session.commit()
    msg = bot.send_message(chat_id, text, parse_mode='markdown')
    bot.register_next_step_handler(msg, commit_translate)


def commit_translate(message):
    """Commit to DB."""
    if message.text.lower() != '/verify':
        if message.text.lower() != '/skip':
            user = session.query(User).filter_by(
                user_id=message.from_user.id).first()
            row = session.query(Data).filter_by(osm_id=user.translate).first()
            row.translation = message.text
            row.translator_id = user.user_id
            session.commit()
        get_translate(message)


bot.polling(none_stop=True)

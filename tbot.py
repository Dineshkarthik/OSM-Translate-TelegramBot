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
    "sqlite:///" + config["db_name"] + ".db?check_same_thread=False",
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


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """/start."""
    bot.send_message(message.chat.id, """\
I can help you translate contents to Tamil seamlessly.

You can control me by sending these commands:

/translate - To start translating.
/verify - To verify translations.""")


@bot.message_handler(commands=['verify'])
def get_verified(message):
    """/verify."""
    chat_id = message.chat.id
    if chat_id not in _dict.keys():
        _dict[chat_id] = {}
        _dict[chat_id]["id"] = 0
    bot.send_chat_action(chat_id, 'typing')
    result = session.query(Data).filter(
        Data.verified == 0, Data.index > _dict[chat_id]["id"]).first()
    text = "Is *%s* a correct translation of *%s*" % (result.translation,
                                                      result.name)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Correct', 'Wrong')
    _dict[chat_id]["verify"] = result.osm_id
    _dict[chat_id]["id"] = result.index
    msg = bot.send_message(
        chat_id, text, reply_markup=markup, parse_mode='markdown')
    bot.register_next_step_handler(msg, commit_verify)


def commit_verify(message):
    """Commit to DB."""
    if message.text.lower() != '/translate':
        if message.text == 'Correct':
            id = _dict[message.chat.id]["verify"]
            row = session.query(Data).filter_by(osm_id=id).first()
            row.verified = 1
            session.commit()
        get_verified(message)


@bot.message_handler(commands=['translate'])
def get_translate(message):
    """/translate."""
    chat_id = message.chat.id
    if chat_id not in _dict.keys():
        _dict[chat_id] = {}
        _dict[chat_id]["id"] = 0
    bot.send_chat_action(chat_id, 'typing')
    result = session.query(Data).filter(
        Data.verified == 0, Data.index > _dict[chat_id]["id"]).first()
    text = "Translation for *%s*\nIf not sure please reply /skip" % result.name
    _dict[chat_id]["translate"] = result.osm_id
    _dict[chat_id]["id"] = result.index
    msg = bot.send_message(chat_id, text, parse_mode='markdown')
    bot.register_next_step_handler(msg, commit_translate)


def commit_translate(message):
    """Commit to DB."""
    if message.text.lower() != '/verify':
        if message.text.lower() != '/skip':
            id = _dict[message.chat.id]["translate"]
            row = session.query(Data).filter_by(osm_id=id).first()
            row.translation = message.text
            session.commit()
        get_translate(message)


bot.polling(none_stop=True)

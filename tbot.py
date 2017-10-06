"""TelegramBot for OSM translation."""
import telebot
from telebot import types
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *

bot = telebot.TeleBot("TOKEN")
db = create_engine("sqlite:///OSM_Tamil_translation_TN.db", echo=False)
Base = declarative_base()
Base.metadata.reflect(db)
Session = sessionmaker(bind=db)
session = Session()


class data(Base):
    """Class for translation table."""
    __table__ = Base.metadata.tables['translation']
    __mapper_args__ = {
        'primary_key': [__table__.c.osm_id]
    }


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
    bot.send_chat_action(message.chat.id, 'typing')
    result = session.query(data).filter_by(verified=0).first()
    text = "Is %s a correct translation of %s" % (result.translation, result.name)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Correct', 'Wrong')
    msg = bot.send_message(
        message.chat.id, text, reply_markup=markup)
    bot.register_next_step_handler(msg, commit_verify)


def commit_verify(message):
    print(message)

bot.polling()

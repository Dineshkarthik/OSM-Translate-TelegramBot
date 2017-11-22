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
available_commands = [
    '/translate', '/verify', '/contribute', '/mystats', '/start',
    '/updateusername', '/remaining', '/leaderboard', '/help', '/broadcast'
]


class Data(Base):
    """Class for translation table."""

    __table__ = Base.metadata.tables['translation']
    __mapper_args__ = {'primary_key': [__table__.c.osm_id]}


class User(Base):
    """Class for user table."""

    __table__ = Base.metadata.tables['users']
    __mapper_args__ = {'primary_key': [__table__.c.user_id]}


def user_exists(user_id):
    """Check if user entry exists in user table."""
    return session.query(exists().where(User.user_id == user_id)).scalar()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """/start."""
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    if not user_exists(user_id):
        msg = bot.send_message(message.chat.id, """\
Dear """ + user_name + """, We appreciate your interest in contributing to OSM.

We keep track of all your contributions, hence need your OSM username,
Please reply with your OSM username.

If you don't have one, Please use the following link and create one
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
    if message.text.lower() not in available_commands:
        if message.text.startswith('/'):
            send_instructions(message)
        else:
            user = User()
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            user.osm_username = message.text
            user.tlg_username = message.from_user.username
            user.user_id = message.from_user.id
            user.verify_count = 0
            user.t_index = 0
            user.translate_count = 0
            user.v_index = 0
            user.is_admin = 0
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
    if message.text.lower() not in available_commands:
        if message.text.startswith('/'):
            send_instructions(message)
        else:
            user = session.query(User).filter_by(
                user_id=message.from_user.id).first()
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
/verify - To verify translations.
/mystats - To get your contribution stats.
/remaining - To get count of remaining untranslated and unverified items.
/leaderboard - To get list of top contributers
/updateusername - To change your OSM username
/help - To view this help message""")
    if user_exists(message.from_user.id):
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        if user.is_admin == 1:
            bot.send_message(
                message.chat.id,
                """\
*Admin Privilege:*

/broadcast - To send message to all users.""",
                parse_mode='markdown')


@bot.message_handler(commands=['verify'])
def get_verified(message):
    """/verify."""
    chat_id = message.chat.id
    if user_exists(message.from_user.id):
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        bot.send_chat_action(chat_id, 'typing')
        result = session.query(Data).filter(
            Data.verified.in_(
                ('-1', '-2', '0', '1', '2')), Data.index > user.v_index,
            Data.translation != None, Data.translator_id == 0).first()
        if result is None:
            bot.send_message(
                chat_id,
                "Dear %s currently there are no items available for you to verify"
                % user.first_name)
            send_instructions(message)
        else:
            text = "%s - %s\nஇது சரியான தமிழாக்கமா?" % (result.name,
                                                        result.translation)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            markup.add('சரி', 'தவறு')
            user.verify = result.osm_id
            user.v_index = result.index
            session.commit()
            msg = bot.send_message(
                chat_id, text, reply_markup=markup, parse_mode='markdown')
            bot.register_next_step_handler(msg, commit_verify)
    else:
        send_welcome(message)


def commit_verify(message):
    """Commit to DB."""
    if message.text.lower() not in available_commands:
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        if message.text == 'சரி':
            row = session.query(Data).filter_by(osm_id=user.verify).first()
            row.verified += 1
            user.verify_count += 1
            session.commit()
            get_verified(message)
        elif message.text == 'தவறு':
            row = session.query(Data).filter_by(osm_id=user.verify).first()
            row.verified -= 1
            user.verify_count += 1
            session.commit()
            get_verified(message)
        else:
            bot.send_message(message.chat.id, """\
Unable to process the command - %s
Please use /help to view all available commands""" % message.text)


@bot.message_handler(commands=['translate'])
def get_translate(message):
    """/translate."""
    chat_id = message.chat.id
    if user_exists(message.from_user.id):
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        bot.send_chat_action(chat_id, 'typing')
        result = session.query(Data).filter(
            Data.verified.in_(('-3', '0')), Data.index > user.t_index,
            Data.translator_id == 0).first()
        if result is None:
            bot.send_message(
                chat_id,
                "Dear %s currently there are no items available for you to translate"
                % user.first_name)
            send_instructions(message)
        else:
            text = "Translation for *%s*\nIf not sure please reply /skip" % result.name
            user.translate = result.osm_id
            user.t_index = result.index
            session.commit()
            msg = bot.send_message(chat_id, text, parse_mode='markdown')
            bot.register_next_step_handler(msg, commit_translate)
    else:
        send_welcome(message)


def commit_translate(message):
    """Commit to DB."""
    if message.text.lower() not in available_commands:
        if message.text.lower() == '/skip':
            get_translate(message)
        elif message.text.startswith('/'):
            bot.send_message(message.chat.id, """\
Unable to process the command - %s
Please use /help to view all available commands""" % message.text)
        else:
            user = session.query(User).filter_by(
                user_id=message.from_user.id).first()
            row = session.query(Data).filter_by(osm_id=user.translate).first()
            row.translation = message.text
            row.translator_id = user.user_id
            user.translate_count += 1
            session.commit()
            get_translate(message)


@bot.message_handler(commands=['mystats'])
def get_stats(message):
    """/mystats."""
    chat_id = message.chat.id
    if user_exists(message.from_user.id):
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        text = "Locations Verified - *%s*\nLocations Translated - *%s*" % (
            user.verify_count, user.translate_count)
        bot.send_message(chat_id, text, parse_mode='markdown')
    else:
        send_welcome(message)


@bot.message_handler(commands=['remaining'])
def get_remaining(message):
    """/remaining."""
    chat_id = message.chat.id
    remaining_verify = session.query(func.count(Data.osm_id)).filter(
        Data.verified.in_(('-1', '-2', '0', '1', '2')),
        Data.translation != None, Data.translator_id == 0).scalar()
    remaining_translate = session.query(func.count(Data.osm_id)).filter(
        Data.verified.in_(('-3', '0')), Data.translator_id == 0).scalar()
    text = "Items to be Verified - *%s*\nItems to be Translated - *%s*" % (
        remaining_verify, remaining_translate)
    bot.send_message(chat_id, text, parse_mode='markdown')


@bot.message_handler(commands=['leaderboard'])
def get_leaderboard(message):
    """/leaderboard."""
    chat_id = message.chat.id
    translate_users = session.query(User.osm_username).order_by(
        User.translate_count.desc()).limit(10).all()
    verify_users = session.query(User.osm_username).order_by(
        User.verify_count.desc()).limit(10).all()
    user_count = session.query(func.count(User.user_id)).filter(
        or_(User.translate_count > 0, User.verify_count > 0)).scalar()
    translate_list = '\n'.join([user.osm_username for user in translate_users])
    verify_list = '\n'.join([user.osm_username for user in verify_users])
    text = "*Contributors - %s*\n*Leaderboard*:\nTop Translators:\n%s\n\nTop Verifiers\n%s" % (
        user_count, translate_list, verify_list)
    bot.send_message(chat_id, text, parse_mode='markdown')


@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    """/broadcast."""
    chat_id = message.chat.id
    if user_exists(message.from_user.id):
        user = session.query(User).filter_by(
            user_id=message.from_user.id).first()
        if user.is_admin == 1:
            text = "Dear Admin, Please reply the message need to be broadcasted"
            msg = bot.send_message(chat_id, text, parse_mode='markdown')
            bot.register_next_step_handler(msg, send_to_all)
        else:
            text = """You don't have admin privilege to broadcast.
Please contact administrator for access."""
            bot.send_message(chat_id, text, parse_mode='markdown')
    else:
        send_welcome(message)


def send_to_all(message):
    """Broadcast a message to all users."""
    if message.text.lower() not in available_commands:
        chat_id = message.chat.id
        text = "Broadcast - Successful."
        for user in session.query(User.user_id).all():
            bot.send_message(user[0], message.text)
        bot.send_message(chat_id, text, parse_mode='markdown')


bot.polling(none_stop=True)

"""TelegramBot for OSM translation."""
import telebot
import sqlite3
import pandas as pd
from telebot import types

bot = telebot.TeleBot("TOKEN")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """/start."""
    bot.send_message(message.chat.id, """\
I can help you translate contents to Tamil seamlessly.

You can control me by sending these commands:

/translate - To start translating.
/verify - To verify translations.""")


@bot.message_handler(commands=['translate'])
def get_translate(message):
    """/translate."""
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('True', 'False')
    msg = bot.send_message(
        message.chat.id, 'Lets start translating', reply_markup=markup)


bot.polling()

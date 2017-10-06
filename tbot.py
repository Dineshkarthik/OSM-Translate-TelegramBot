"""TelegramBot for OSM translation."""
import telebot

bot = telebot.TeleBot("TOKEN")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """/start."""
    bot.send_message(
        message.chat.id,
        'I can help you translate contents to Tamil seamlessly\n\nYou can contril me by sending these commands:\n\n/translate - To start translating.\n/verify - To verify translations.'
    )


@bot.message_handler(commands='translate')
def get_translate(message):
    """/translate."""
    bot.send_message(message.chat.id, 'Lets start translating')


# @bot.message_handler(func=lambda message: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

bot.polling()

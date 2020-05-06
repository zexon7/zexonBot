from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import logging

#logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#function
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def start(update, context):
    context.message.reply_text("Welcome to my awesome bot!")
    logging.info('[userMessage]: %s' % context.message.text)

def hello(update, context):
    context.message.reply_text('Hello, {}'.format(context.message.from_user.first_name))
    logging.info('[userMessage]: %s' % context.message.text)

def getUrl(update, context):
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("zexon7", url = "https://github.com/zexon7")
    ]])
    update.send_message(context.message.chat.id, "Github", reply_markup = reply_markup)
    logging.info('[userMessage]: %s' % context.message.text)

#start bot
if __name__ == '__main__':
    #Bot's API token
    updater = Updater('')

    #for quick access
    dp = updater.dispatcher

    #handler
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('hello', hello))
    dp.add_handler(CommandHandler('url', getUrl))

    updater.start_polling()
    updater.idle()
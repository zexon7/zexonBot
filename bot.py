from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

#check bug
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#Bot's API token
updater = Updater('')

#for quick access
dispatcher = updater.dispatcher

def start(update, context):
    context.message.reply_text("Welcome to my awesome bot!")

def hello(update, context):
    context.message.reply_text('Hello, {}'.format(context.message.from_user.first_name))

#/start
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('hello', hello))

#start bot
updater.start_polling()
updater.idle()
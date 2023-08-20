import logging

import telegram
from environs import Env
from telegram import Update, BotCommand
from telegram.ext import CallbackContext, CommandHandler, Updater, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():
    env = Env()
    env.read_env()
    bot_token = env.str('TG_TOKEN')
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    def start(update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Здравствуйте")

    def echo(update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

    dp.add_handler(start_handler)

    updater.start_polling()
    dp.add_handler(echo_handler)


if __name__ == '__main__':
    main()

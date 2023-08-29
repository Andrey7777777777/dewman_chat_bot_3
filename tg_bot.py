import logging
import random
import os
import argparse

import telegram
from environs import Env
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater, MessageHandler, Filters, ConversationHandler, RegexHandler
import redis

from text_tools import get_questions_answers

logger = logging.getLogger(__name__)

PLAYING, WIN, ANSWER = range(3)


def main():

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    default_file_path = (os.path.join(os.getcwd(), 'quiz-questions'))

    parser = argparse.ArgumentParser(description='Запуск скрипта')
    parser.add_argument(
        '-fp',
        '--file_path',
        help='Укажите путь к файлу',
        nargs='?', default=default_file_path, type=str
    )
    args = parser.parse_args()
    file_path = args.file_path
    quiz = get_questions_answers(filepath=file_path)
    env = Env()
    env.read_env()
    bot_token = env.str('TG_TOKEN')
    chat_id = env.str('TG_CHAT_ID')
    host = env.str('REDIS_HOST')
    port = env.int('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    redis_db = redis.Redis(host=host, port=port, password=redis_password)
    bot = telegram.Bot(token=bot_token)
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    def start(update: Update, context: CallbackContext):
        custom_keyboard = [['Новый вопрос', 'Сдаться'],
                           ['Мой счет']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.send_message(chat_id=chat_id,
                         text="ЭТО Викторина",
                         reply_markup=reply_markup)
        return WIN

    def nev_question(update: Update, context: CallbackContext):
        random_question_answer = random.choice(list(quiz.items()))
        question = random_question_answer[0]
        answer = random_question_answer[1]
        redis_db.set('question', question)
        redis_db.set('answer', answer)
        context.bot.send_message(chat_id=update.effective_chat.id, text=question)
        return ANSWER

    def answer(update: Update, context: CallbackContext):
        answer = redis_db.get('answer').decode('utf-8')
        answer_user = update.message.text
        if answer_user.strip().lower() == answer.strip().lower():
            context.bot.send_message(chat_id=update.effective_chat.id, text='Поздравляю ваш ответ правильный!!!')
            return WIN
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Не правильно! Правильный ответ: {answer}')
            return PLAYING

    def surrender(update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text='ОЧЕНЬ ЖАЛЬ!!!')
        return ConversationHandler.END

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={PLAYING: [RegexHandler('^Новый вопрос$', nev_question),
                          RegexHandler('^Сдаться$', surrender),
                          MessageHandler(Filters.text, nev_question)],
                ANSWER: [MessageHandler(Filters.text & (~Filters.command), answer),
                         RegexHandler('^Сдаться$', surrender)],
                WIN: [RegexHandler('^Новый вопрос$', nev_question),
                      RegexHandler('^Сдаться$', surrender)]
                },
        fallbacks=[CommandHandler('surrender', surrender)])

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

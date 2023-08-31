import logging
import random
import os
import argparse
from functools import partial
import telegram
from environs import Env
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Updater, MessageHandler, Filters, ConversationHandler, RegexHandler
import redis

from text_tools import get_questions_answers

logger = logging.getLogger(__name__)

PLAYING, WIN, ANSWER = range(3)


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="ЭТО Викторина",
                             reply_markup=reply_markup)
    return WIN


def get_new_question(update: Update, context: CallbackContext, redis_db, quiz, chat_id):
    random_question_answer = random.choice(list(quiz.items()))
    question, answer = random_question_answer
    redis_db.set(f'tg_question {chat_id}', question)
    redis_db.set(f'tg_answer {chat_id}', answer)
    context.bot.send_message(chat_id=update.effective_chat.id, text=question)
    return ANSWER


def answer(update: Update, context: CallbackContext, redis_db, chat_id):
    answer = redis_db.get(f'tg_answer {chat_id}').decode('utf-8')
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
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    partial_get_new_question = partial(get_new_question, redis_db=redis_db, quiz=quiz, chat_id=chat_id)
    partial_answer = partial(answer, redis_db=redis_db, chat_id=chat_id)


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={PLAYING: [RegexHandler('^Новый вопрос$', partial_get_new_question),
                          RegexHandler('^Сдаться$', surrender),
                          MessageHandler(Filters.text, get_new_question)],
                ANSWER: [MessageHandler(Filters.text & (~Filters.command), partial_answer),
                         RegexHandler('^Сдаться$', surrender)],
                WIN: [RegexHandler('^Новый вопрос$', partial_get_new_question),
                      RegexHandler('^Сдаться$', surrender)]
                },
        fallbacks=[CommandHandler('surrender', surrender)])

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

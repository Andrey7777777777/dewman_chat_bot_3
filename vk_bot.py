import logging
import random
import os
import argparse

from environs import Env

import redis
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from text_tools import get_questions_answers

logger = logging.getLogger(__name__)


def start(event, vk_api, keyboard):
    vk_api.messages.send(
        user_id=event.user_id,
        message='Привет я бот для викторин',
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )


def nev_question(vk_api, event, redis_db, keyboard, quiz):
    random_question_answer = random.choice(list(quiz.items()))
    question = random_question_answer[0]
    answer = random_question_answer[1]
    redis_db.set('question', question)
    redis_db.set('answer', answer)
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000))


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
    bot_vk_token = env.str('VK_TOKEN')
    host = env.str('REDIS_HOST')
    port = env.int('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    redis_db = redis.Redis(host=host, port=port, password=redis_password)
    while True:
        try:
            vk_session = vk.VkApi(token=bot_vk_token)
            vk_api = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            logger.info('Бот запущен')
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
            keyboard.add_button('Сдаться', color=VkKeyboardColor.POSITIVE)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if event.text == "Начать" or event.text == "начать":
                        start(event, vk_api, keyboard)
                    elif event.text == "Новый вопрос":
                        nev_question(vk_api, event, redis_db, keyboard, quiz)
                    elif event.text == "Сдаться":
                        answer = redis_db.get('answer').decode('utf-8')
                        vk_api.messages.send(
                            user_id=event.user_id,
                            message=f'Правильный ответ: {answer}',
                            keyboard=keyboard.get_keyboard(),
                            random_id=random.randint(1, 1000))
                    else:
                        if event.text.strip().lower() == answer.strip().lower():
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message='Позравляю!!! Павельно!!!',
                                keyboard=keyboard.get_keyboard(),
                                random_id=random.randint(1, 1000))
                        else:
                            vk_api.messages.send(
                                user_id=event.user_id,
                                message=f'Ответ не верный! Правильный ответ: {answer}',
                                keyboard=keyboard.get_keyboard(),
                                random_id=random.randint(1, 1000))
        except Exception as error:
            logger.exception(f'Бот упал с ошибкой: {error}')


if __name__ == '__main__':
    main()
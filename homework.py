import logging
import requests
from http import HTTPStatus
from time import time, sleep
from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import CommandHandler, Updater
import os
import sys
from dotenv import load_dotenv
from logging import StreamHandler
import exceptions


logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    level=logging.DEBUG)

handler = StreamHandler(sys.stdout)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


logger.debug("A DEBUG message")
logger.info("An INFO message")
logger.warning("A WARNING message")
logger.error("An ERROR message")
logger.critical("A CRITICAL message")

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

#print(PRACTICUM_TOKEN)
print(TELEGRAM_TOKEN)
print(TELEGRAM_CHAT_ID)


RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
bot_fav = Bot(token=TELEGRAM_TOKEN)
old_message = ''


def send_message(bot, message):
    global old_message
    try:
        if old_message != message:
            bot.send_message(TELEGRAM_CHAT_ID, message)
            old_message = message
            logging.info(f'Сообщение успешно отправлено: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе API: {error}')
        send_message(bot_fav, error)
    if response.status_code != HTTPStatus.OK:
        error = f'Ошибка при запросе API: {response.status_code}'
        logging.error(error)
        send_message(bot_fav, error)
        raise HTTPStatus.HTTPStatusException('Ошибка доступа к API')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    print(type(response))    
    if isinstance(response, list) and len(response) == 1:
        response = response[0]
    hw_list = response.get('homeworks', [])
    if hw_list is None:
        raise exceptions.CheckResponseException('Список домашних заданий пуст')
    if not isinstance(hw_list, list):
        error = 'Ответ API не является списком'
        logging.error(error)
        raise Exception(error)
    if len(hw_list) == 0:
        raise exceptions.CheckResponseException(
            'Домашнего задания нет за данный промежуток времени')
    else:
        return hw_list


def parse_status(homework):
#    try:
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
#    except KeyError as error:
#        logging.error(f'Ошибка при получении списка работ: {error}')
#        send_message(bot_fav, error)
    if homework_status is None:
        error = 'Ошибка, отсутствует статус домашней работы'
        logging.error(error)
        send_message(bot_fav, error)
    if homework_name is None:
        error = 'Ошибка, пустое значение homework_name'
        logging.error(error)
        send_message(bot_fav, error)
        raise KeyError(error)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        error = 'Ошибка, неизвестное значение status'
        logging.error(error)
        send_message(bot_fav, error)
        raise KeyError(error)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        logging.critical('Ошибка, отсутствуют переменные окружения')
        return False
    return True


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time()) - 1209600
    previous_status = None
    bot = Bot(token=TELEGRAM_TOKEN)

    if not check_tokens():
        exit()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(type(response))
            homeworks = check_response(response)
            print(type(homeworks))
            current_timestamp = response.get('current_date', [])
            status = homeworks[0].get('status')
            if status != previous_status:
                previous_status = status
                message = parse_status(homeworks[0])
                send_message(bot, message)
        except exceptions.CheckResponseException as error:
            logging.info(f'Обновление статуса: {error}')
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, error)
        else:
            logger.debug('Работа программы без замечаний')
        finally:
            sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

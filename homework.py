import logging
import requests
from time import time, sleep
from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import CommandHandler, Updater
import os
import sys
import dotenv
#from dotenv import load_dotenv
from logging import StreamHandler
import exceptions


# Здесь задана глобальная конфигурация для всех логгеров
logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# А тут установлены настройки логгера для текущего файла - example_for_log.py
logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого логи будут сохраняться в файл
logger.setLevel(logging.INFO)
# Указываем обработчик логов
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


dotenv.load_dotenv()

# AQAAAAAAJywxAAYckRc5OHVyEUGIrjVI49EoYug
PRACTIKUM_TOKEN = os.getenv('PRACTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

#print(PRACTICUM_TOKEN)
print(TELEGRAM_TOKEN)
print(TELEGRAM_CHAT_ID)


RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTIKUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        # response.status_code = 500
        if response.status_code != 200:
            message = f'Ошибка в работе API код: {response.status_code}'
            logging.error(message)
    except Exception as error:
        message = f'Сбой при работе API Yandex_Praktikum ошибка: {error}'
        logging.error(message)
    return response.json()


def check_response(response):
    try:
        hw_list = response.get('homeworks', [])
    except IndexError as error:
        logging.error(f'Error while getting list of homeworks: {error}')
        print('1')
    except KeyError as error:
        logging.error(f'Error while getting list of homeworks: {error}')
        print('1')
    except Exception as error:
        logging.error(f'Error while getting list of homeworks: {error}')
        print('3')
        print('Error while getting list of homeworks')
    if hw_list is None:
        raise exceptions.CheckResponseException('Списка домашних заданий нет')
        print(4)
    if not isinstance(hw_list, list):
        print(0)
#        raise exceptions.CheckResponseException(
#            'Ответ Api не является списком')
    if len(hw_list) == 0:
        print(5)
        raise exceptions.CheckResponseException(
            'Домашнего задания нет за данный промежуток времени')

    else:
        return hw_list


def parse_status(homework):
    homework_name = homework[0].get('homework_name')
    homework_status = homework[0].get('status')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTIKUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        return False
    return True


def main():
    """Основная логика работы бота."""

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time()) - 1209600
    previous_status = None

    check_tokens()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(response)
            homeworks = check_response(response)
            current_timestamp = response.get('current_date', [])
            #homeworks[0].get('current_date')
            status = homeworks[0].get('status')
            if status != previous_status:
                previous_status = status
                message = parse_status(homeworks)
                send_message(bot, message)
            else:
                sleep(RETRY_TIME)
        except exceptions.CheckResponseException as error:
            message = f'Обновление статуса: {error}'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            sleep(RETRY_TIME)
        else:
            logger.debug('Пока что всё работает хорошо')


if __name__ == '__main__':
    main()

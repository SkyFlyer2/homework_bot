import logging
import requests
from time import time, sleep
from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import CommandHandler, Updater
import os
import sys
from dotenv import load_dotenv
from logging import StreamHandler


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


load_dotenv()

# AQAAAAAAJywxAAYckRc5OHVyEUGIrjVI49EoYug
PRACTIKUM_TOKEN = os.getenv('PRACTIUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

#print(PRACTICUM_TOKEN)
print(TELEGRAM_TOKEN)
print(TELEGRAM_CHAT_ID)


RETRY_TIME = 600
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
    else:
        return hw_list


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    #HOMEWORK_STATUSES

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTIKUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        return False
    return True


def main():
    """Основная логика работы бота."""

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time())

    check_tokens()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            print(response)
            homeworks = check_response(response)

            current_timestamp = homeworks[0].get('current_date')
            for homework in homeworks:
                message = parse_status(homeworks)
                send_message(bot, message)

            sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            sleep(RETRY_TIME)
        else:
            logger.DEBUG('Пока что всё работает хорошо')


if __name__ == '__main__':
    main()

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


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе API: {error}')
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Ошибка при запросе API: {response.status_code}')
        raise HTTPStatus.HTTPStatusException('Ошибка доступа к API')
    return response.json()


def check_response(response):

#    hw_list = {}
    try:
        hw_list = response['homeworks']
    except IndexError as error:
        logging.error(f'Error while getting list of homeworks: {error}')
    except KeyError as error:
        logging.error(f'Error while getting list of homeworks: {error}')
        print('1')
    #except Exception as error:
    #    logging.error(f'Error while getting list of homeworks: {error}')
    #    print('Error while getting list of homeworks')
    if hw_list is None:
        #raise exceptions.CheckResponseException('Списка домашних заданий нет')
        print(4)
    if not isinstance(hw_list, list):
        print(0)
        raise Exception('Ответ Api не является списком')
    if len(hw_list) == 0:
        raise exceptions.CheckResponseException(
            'Домашнего задания нет за данный промежуток времени')

    else:
        return hw_list


def parse_status(homework):
    try:
        homework_name = homework[0].get('homework_name')
        homework_status = homework[0].get('status')
        print(homework_status)
    except KeyError as error:
        logging.error(f'Error while getting list of homeworks: {error}')
#        raise KeyError('')
    if homework_status is None:
        logging.error(f'Error while getting list of homeworks: {error}')
#        raise KeyError('Ошибка, пустое значение status')
    if homework_name is None:
        logging.error('Ошибка, пустое значение homework_name')
        raise KeyError

    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        logging.info('Статус домашней работы неизвестен')
        raise KeyError('Ошибка, неизвестное значение status')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID is None:
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time()) - 1209600
    previous_status = None

    if not check_tokens():
        exit()

    while True:
        try:
            response = get_api_answer(current_timestamp)
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
            logging.info(f'Обновление статуса: {error}')
            sleep(RETRY_TIME)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            sleep(RETRY_TIME)
        else:
            logger.debug('Работа программы без замечаний')


if __name__ == '__main__':
    main()

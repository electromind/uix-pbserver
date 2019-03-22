import logging
import os
import pathlib
from datetime import datetime
import platform
import mysql.connector as db
import time
import re


def get_db():
    try:
        db_conn = db.connect(
            user='root',
            password='password',
            database='whitelist',
            host='localhost')
        db_cursor = db_conn.cursor()
        return db_conn, db_cursor
    except ConnectionError as err:
        print(f'{get_timestring()}DB Connection Error\n{get_timestring()}{err}')
        print(f'{get_timestring()}5 sec to reconnect')
        time.sleep(5)
        get_db()


def is_valid_key(key: str):
    if key and (len(key) == 32 and re.match(r"^[A-Za-z0-9]*$", key)):
        return True
    else:
        return False


def get_datestring():
    return datetime.strftime(datetime.now(), '%d-%m-%Y')

def get_timestring():
    return datetime.strftime(datetime.now(), '%H:%M:%S:%f\t')


class Logger:
    def __init__(self):
        self.__logger_format = '[%(asctime)s] [%(levelname)s]) %(message)s'
        # self.__logger_format = '%(asctime)s  %(levelname)-9.9s %(message)-70.70s  %(module)s.py:%(lineno)d'
        self.__logger_date_format = '%d-%b-%y %H:%M:%S'
        self.__logger_level = logging.INFO
        if platform.system() == 'Windows':
            separator = '\\'
        else:
            separator = '/'
        tmp = str(__file__).replace('.py', '_').split(separator)
        self.__name = ''.join([tmp[len(tmp) - 1], get_datestring(), '.log'])
        self.__logfile_path = pathlib.Path('\\'.join([os.path.dirname(__file__), 'log']))
        if not os.path.exists(self.__logfile_path):
            os.mkdir(self.__logfile_path)
        self.__path_to_log = self.__logfile_path / self.__name
        f = self.__path_to_log.open('w')
        f.close()

    def get_log(self, name=None, log_level=None, log_format=None, log_date_format=None):
        if name is None:
            name = self.__name
        if log_level is None:
            log_level = self.__logger_level
        if log_format is None:
            log_format = self.__logger_format
        if log_date_format is None:
            log_date_format = self.__logger_date_format
        logging.basicConfig()
        logger = logging.getLogger(name=name)
        logger.setLevel(log_level)
        formatter = logging.Formatter(log_format, log_date_format)
        logfile = logging.FileHandler(filename=self.__path_to_log, encoding='utf-8')
        logstream = logging.StreamHandler()
        logger.addHandler(logfile)
        logger.addHandler(logstream)

        for handler in logger.handlers:
            handler.setFormatter(formatter)
            handler.setLevel(log_level)
        return logger


if __name__ == '__main__':
    a = Logger()
    logger = a.get_log()




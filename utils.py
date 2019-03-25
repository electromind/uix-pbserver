import logging
import os
import pathlib
from datetime import datetime
import platform
import mysql.connector as db
import time
import re
import json


def _get_db():
    db_conn = db.connect(
        user='root',
        password='gigaset1',
        database='whitelist',
        host='localhost')
    if db_conn.is_connected():
        db_conn.autocommit = True
        cur = db_conn.cursor()
        cur.execute("create table userkey(`key` varchar(32) null, column_2 int null);")
        return db_conn
    else:
        return None


def get_whitelisted():
    userlist = None
    db = _get_db()
    if db is None:
        print(f'{get_timestring()}DB Connection Error')
        print(f'{get_timestring()}5 sec to reconnect')
        time.sleep(5)
        _get_db()
    else:
        cur = db.cursor()

        cur.execute("SELECT `keys` FROM whitelist.users")
        try:
            userlist = json.loads(cur.fetchall())
            return userlist
        except Exception as err:
            print(err)
            return None

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
    def __init__(self, name: str):
        self.__logger_format = '[%(asctime)s] [%(levelname)s]) %(message)s'
        # self.__logger_format = '%(asctime)s  %(levelname)-9.9s %(message)-70.70s  %(module)s.py:%(lineno)d'
        # self.__logger_date_format = '%d-%b-%y %H:%M:%S'
        self.__logger_level = logging.INFO
        if platform.system() == 'Windows':
            separator = '\\'
        else:
            separator = '/'
        tmp = str(__file__).replace('.py', '_').split(separator)
        self.__name__ = ''.join([tmp[len(tmp) - 1], get_datestring(), '.log'])
        self.__logfile_path = pathlib.Path('\\'.join([os.path.dirname(__file__), 'log']))
        if not os.path.exists(self.__logfile_path):
            os.mkdir(self.__logfile_path)
        self.__path_to_log = self.__logfile_path / self.__name__
        f = self.__path_to_log.open('w')
        f.close()

    def get_log(self, name=None, log_level=None, log_format=None, log_date_format=None):
        if name is None:
            name = self.__name__
        if log_level is None:
            log_level = self.__logger_level
        if log_format is None:
            log_format = self.__logger_format
        # if log_date_format is None:
        #     log_date_format = self.__logger_date_format
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



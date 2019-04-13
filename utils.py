import json
import logging
import os
import pathlib
import re
import time
from datetime import datetime

import mysql.connector as db


class Logger(logging.Logger):
    def __init__(self, name: str, loglevel=logging.INFO):
        super().__init__(name=name, level=loglevel)
        FORMAT = ('%(asctime)s %(levelname)s %(message)s')
        self.__format__(FORMAT)
        self.__logfile_name = ''.join([name, get_datestring(), '.log'])
        self.__logdir_path = pathlib.Path('/'.join([os.path.dirname(__file__), 'log']))
        if not os.path.exists(self.__logdir_path):
            os.mkdir(self.__logdir_path)
        self.__path_to_log = self.__logdir_path / self.__logfile_name

        if not os.path.isfile(self.__path_to_log):
            f = self.__path_to_log.open('w')
            f.close()
        logfile_handler = logging.FileHandler(filename=self.__path_to_log, encoding='utf-8')
        self.addHandler(logfile_handler)
        logstream = logging.StreamHandler()
        self.addHandler(logstream)


def _get_db():
    db_conn = db.connect(
        user='root',
        password='password',
        database='whitelist',
        host='localhost')
    if db_conn.is_connected():
        db_conn.autocommit = True
        # cur = db_conn.cursor()
        # cur.execute("create table userkey(`key` varchar(32) null, column_2 int null);")
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

        cur.execute("SELECT userkey FROM whitelist.users")
        try:
            userlist = json.dumps([x[0] for x in cur.fetchall()])
            return userlist
        except Exception as err:
            print(err)
            return None


def is_valid_key(key: str):
    if key and len(key) == 32 and re.match(r"^[A-Za-z0-9]*$", key):
        return True
    else:
        return False


def get_datestring():
    return datetime.strftime(datetime.now(), '%d-%m-%Y')


def get_timestring():
    return datetime.strftime(datetime.now(), '%H:%M:%S:%f\t')




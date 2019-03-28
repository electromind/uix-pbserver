import logging
import os
import pathlib
from datetime import datetime
import paramiko
import mysql.connector as db
import time
import re
import json
import settings as s
import apscheduler.schedulers.background as shadow_sync
from apscheduler.triggers import interval as running_pause

def get_datestring():
    return datetime.strftime(datetime.now(), '%d-%m-%Y')


def get_timestring():
    return datetime.strftime(datetime.now(), '%H:%M:%S:%f\t')


class Logger(logging.Logger):
    def __init__(self, name: str, loglevel=logging.INFO):
        super().__init__(name=name, level=loglevel)
        format('%(levelname)s %(message)s')
        # self.__logger_format = '%(levelname)s %(message)s'
        # if platform.system() == 'Windows':
        #     separator = '\\'
        # else:
        #     separator = '/'
        # # tmp = str(__file__).replace('.py', '_').split(separator)

        self.__logfile_name = ''.join([name, get_datestring(), '.log'])
        self.__logdir_path = pathlib.Path('\\'.join([os.path.dirname(__file__), 'log']))
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


logger = Logger('utils_')


def _get_db():
    db_conn = db.connect(
        user='root',
        password='gigaset1',
        database='whitelist',
        host='localhost')
    if db_conn.is_connected():
        # db_conn.autocommit = True
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

        cur.execute("SELECT `account_key` FROM whitelist.user_keys")
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


def sync_remote_keys():
    logger.info('start update keys')
    try:
        pk = paramiko.RSAKey.from_private_key_file(
            filename=os.getcwd() + s.WL_KEY_FILE_NAME,
            password=s.WL_PASS
        )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=s.WL_HOST,
            username=s.WL_USER,
            pkey=pk
        )
        sftp = ssh.open_sftp()
        pk = json.load(sftp.open(s.WL_FILE_NAME))
        key_list = (pk['ACCOUNT_KEY'])
        ssh.close()
        if key_list:
            updated_keys = 0
            stored_keys = 0
            db = _get_db()
            cur = db.cursor()
            cur.execute("SELECT `account_key` FROM whitelist.user_keys")
            my_keylist = [x[0] for x in cur.fetchall()]
            for key in key_list:
                if key in my_keylist:
                    stored_keys += 1
                    continue
                else:
                    cur.execute("INSERT INTO whitelist.user_keys(account_key) VALUES(%s)",
                                (key, ))
                    db.commit()
                    logger.info(f'{get_timestring()}Insert new user: {key}')
                    updated_keys += 1

            logger.info(f"{updated_keys} key(s) of {len(key_list)} total keys, updated successfully\t{stored_keys}keys was stored before")
        return key_list if key_list else None
    except Exception as e:
        print(f'Remote WL synchronization error.\n{e}')

shadow_sync = shadow_sync.BackgroundScheduler()
shadow_sync.add_job(sync_remote_keys, trigger=running_pause.IntervalTrigger(seconds=10))
shadow_sync.start()



import json
import mysql.connector
import datetime
import socket
import os
import re
import paramiko
import utils

import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread


class Server(Thread):

    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()

    @staticmethod
    def is_valid_key(key: str):
        if len(key) == 32 and re.match(r"^[A-Za-z0-9]*$", key):
            return True
        else:
            return False

    def receive(self, connection, sender_ip):
        print(f'Connection from: {sender_ip}')
        raw_data = b''

    def start(self):
        print("Bot started")
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('109.104.178.163', 2511))
        conn, addr = sock.accept()
        sock.listen(200)
        while True:


            while True:
                tmp = conn.recv(1024)
                if not tmp:
                    break
                else:
                    raw_data += tmp
            if raw_data:
                data = raw_data.decode('utf-8')

                if 'auth_me:' in data:
                    await asyncio.ensure_future(coro_or_future=self.auth(userkey=data.replace('auth_me:', ''), conn=conn),loop=self.loop)
                elif 'uix_tx:' in data:
                    await asyncio.ensure_future(coro_or_future=self.transaction(data=data.replace('uix_tx:', '')), loop=self.loop)

    async def auth(self, userkey, conn):
        await asyncio.sleep(0)
        if conn and Server.is_valid_key(userkey):
            conndb, cur = self.()
            cur.execute("SELECT * FROM user_keys WHERE account_key = %s", (userkey,))
            user = cur.fetchone()
            conndb.close()
            if user:
                conn.send(b'True')
                self.logger(f'Auth - OK: {userkey}')
            else:
                conn.send(b'False')
                self.logger(f'Auth - Fail: User: {userkey} is not whitelisted')

    async def transaction(self, data):
        await asyncio.sleep(0)
        try:
            js = json.loads(data)
        except json.JSONDecodeError:
            return False

        userkey = (js['user_id'])
        trx = (js['tx_list'])
        if len(userkey) == 32 and re.match(r"^[A-Za-z0-9]*$", userkey):
            conn, cur = self.database()
            for item in trx:
                cur.execute('''INSERT INTO trx(user_id, tx_id, create_date, amount, price, side, mined, revd)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                ''', (userkey, item.get('tx_id'), item.get('create_date'), item.get('amount'), item.get('price'),
                      item.get('side'), item.get('mined'), item.get('revd')))
                conn.commit()
                self.logger(f"transaction {item.get('tx_id')} from {userkey[:4]} saved to database")
            conn.close()
            del data
        except NameError:
            del data
        except Exception as e:
            print(f"transaction (save to bd)\t{e}\n{data}")
            del data

    async def synckey(self):
        pk = paramiko.RSAKey.from_private_key_file(filename=os.getcwd() + '/private', password='@e1ectromind')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname='209.250.232.25', username='mrwhite', pkey=pk)
        sftp = ssh.open_sftp()
        pk = json.load(sftp.open('wl.json'))
        key_list = (pk['ACCOUNT_KEY'])
        ssh.close()
        await asyncio.sleep(0)
        conn, cur = self.database()
        my_keylist = cur.execute('''SELECT * FROM user_keys''')
        cur.fetchall()
        updated_keys = 0
        for key in key_list:
            if key in my_keylist:
                continue
            # cur.execute("SELECT * FROM user_keys WHERE account_key = %s", (key,))
            # user = cur.fetchone()
            else:
                cur.execute("INSERT INTO user_keys(account_key, create_date) VALUES(%s,%s)",
                            (key, int(datetime.datetime.now().timestamp())))
                conn.commit()
                print(f'Insert new user: {key}')
                updated_keys += 1
        if i > 0:
            print(f"{updated_keys} key(s) of {len(my_keylist)} total keys, updated successfully")
        cur.close()
        conn.close()
        return True

    async def get_db(self):
        conn = mysql.connector.connect(host=self.__host, database=self.__database, user=self.__user, password=self.__password)
        cur = conn.cursor()
        await asyncio.sleep(0)
        return conn, cur

    def connect(self, database, user='root', password='password', host='localhost'):
        self.__user = user
        self.__password = password
        self.__host = host
        self.__database = database
        self.__log_path = '/log'
        self.__port = 2511

    def date(self):
        return datetime.strftime(datetime.now(), '%d-%m-%Y')

    def get_time(self):
        return datetime.strftime(datetime.now(), '%H:%M:%S: ')

    def logpath(self):
        return os.getcwd() + self.__log_path

    def logger(self, message):
        print(self.time() + message)
        if not os.path.exists(self.logpath()):
            os.mkdir(self.logpath())
        with open(self.logpath() + '/' + self.date() + '.log', 'a') as file:
            file.write(self.time() + message + '\r\n')


if __name__ == '__main__':
    server = Server()
    server.connect(user='root', password='password', database='whitelist', host='localhost')

    sync = BackgroundScheduler(daemon=True)
    sync.add_job(server.synckey, trigger='interval', seconds=59)
    sync.start()

    server.start()

#!/usr/bin/env python3
import logging
import re
import socketserver
from utils import get_db, is_valid_key
from utils import Logger
from utils import get_timestring as t_now

HOST = '10.0.1.5'
PORT = 2512

# BUFFER_SIZE = 1024


class ReqHandler(socketserver.StreamRequestHandler):
    def setup(self):
        self.BUFFER_SIZE = 1024
        logger = Logger()
        self.log = logger.get_log(name='handler')

    def finish(self):
        self.request.close()

    def handle(self):
        msg = self.get_client_msg(self.BUFFER_SIZE)
        self.log.info(f'{t_now()}Client: {self.client_address[0]} sent data: {msg[:20]}')

        if 'auth_me:' in msg:
            userkey = msg.replace('auth_me:', '')
            if self.auth(userkey):
                self.send_client_msg('True')
            else:
                self.send_client_msg('False')

        self.send_client_msg(msg)
        # self.log.info(f'{t_now()}Server responded to client: {self.client_address[0]}')

    def get_client_msg(self, buff):
        data = self.request.recv(buff)

        return data.decode('utf-8')

    def send_client_msg(self, msg: str):
        message = bytes(msg, encoding='utf-8')
        resp = self.request.send(message)


    def auth(self, userkey: str):
        if is_valid_key(userkey):
            conndb, cur = get_db()
            cur.execute("SELECT * FROM whitelist.users WHERE users.`keys` = %s", (userkey,))
            user = cur.fetchone()
            conndb.close()
            if user:
                self.log.info(f'{t_now()}Auth - OK: {userkey}')
                return True
            else:
                self.log.info(f'{t_now()}Auth - Fail: User: {userkey} is not whitelisted')
                return False
        else:
            return False


class EchoServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def process_request(self, request, client_address):
        logging.info('Connection from client %r', client_address)
        super().process_request(request, client_address)


if __name__ == '__main__':
    with EchoServer((HOST, PORT), ReqHandler) as server:
        # server.timeout = 1
        # server.handle_timeout()
        server.serve_forever()

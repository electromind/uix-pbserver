#!/usr/bin/env python3
import logging
import json
import socketserver
from utils import get_whitelisted, is_valid_key, _get_db
from utils import Logger
from utils import get_timestring as t_now
from settings import Settings


class ReqHandler(socketserver.StreamRequestHandler):
    settings = Settings()
    log = Logger('core').get_log()
    def setup(self):
        print(self.client_address)
        addr = self.settings.address
        whitelisted = get_whitelisted()
        if whitelisted is None:
            pass
        else:
            self.whitelist = whitelisted
            print(whitelisted)

    def finish(self):
        self.request.close()

    def handle(self):
        msg = self.get_client_msg(self.settings.buff_size)
        self.log.info(f'{t_now()}Client: {self.client_address[0]} sent data: {msg[:20]}')

        if 'auth_me:' in msg:
            userkey = msg.replace('auth_me:', '')
            if self.auth(userkey):
                self.send_client_msg('True')
            else:
                self.send_client_msg('False')
        elif '_online:' in msg:
            return self.send_client_msg('True')


        self.send_client_msg(msg)
        # self.log.info(f'{t_now()}Server responded to client: {self.client_address[0]}')

    def request_manager(self, req: str):
        r = json.loads(req)

    def get_client_msg(self, buff):
        data = self.request.recv(buff)

        return data.decode('utf-8')

    def send_client_msg(self, msg: str):
        message = bytes(msg, encoding='utf-8')
        resp = self.request.send(message)

    def auth(self, userkey: str):
        if is_valid_key(userkey):
            conndb = _get_db()
            cur = conndb.cursor()
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

class PBStatServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def process_request(self, request, client_address):
        logging.info('Connection from client %r', client_address)
        super().process_request(request, client_address)


if __name__ == '__main__':
    settings = Settings()
    with PBStatServer(settings.address, ReqHandler) as server:
        # server.timeout = 1
        # server.handle_timeout()
        server.serve_forever()

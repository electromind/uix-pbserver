#!/usr/bin/env python3
import logging
from socketserver import StreamRequestHandler, ThreadingTCPServer
from datetime import datetime
from settings import Settings as settings
from pprint import pprint
from utils import Logger
from utils import get_timestring as t_now
from utils import get_whitelisted, is_valid_key, sync_remote_keys, insert_in_db

logger = Logger('server_')
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT)
app_data = settings(debug=False)
calls = 0

class ReqHandler(StreamRequestHandler):

    def finish(self):
        self.request.close()

    def handle(self):
        global calls
        calls += 1
        msg = self.get_client_msg(app_data.buff_size)
        logger.info(f'Request from:\t{self.client_address[0]}\t{msg}')
        if 'auth#' in msg:
            userkey = msg.replace('auth#', '')
            if self.auth(userkey):
                self.send_client_msg('True')
            else:
                self.send_client_msg('False')
        elif 'online#' in msg:
            return self.send_client_msg('True')
        elif 'tx_stat#' in msg:
            raw_tx_list = msg.replace('tx_stat#', '')
            tx_list = raw_tx_list.split('#')
            insert_in_db(tx_list[0], tx_list[1])
            logger.info(raw_tx_list)
        elif 'sync#' in msg:
            userkey = msg.replace('sync#', '')
            logger.info(self.sync())
        else:
            return self.send_client_msg('False')

    def get_client_msg(self, buff):
        data = self.request.recv(buff)
        return data.decode('utf-8')

    def sync(self):
        sync_remote_keys()

    def send_client_msg(self, msg: str):
        message = bytes(msg, encoding='utf-8')
        resp = self.request.send(message)

    def auth(self, userkey: str):
        if is_valid_key(userkey):
            if userkey in self.server.wl:
                logger.info(f'OK: {userkey}')
                return True
            else:
                logger.info(f'Fail: {userkey} not whitelisted')
                return False
        else:
            return False


class PBStatServer(ThreadingTCPServer):
    def __init__(self, handler: ReqHandler, addr: tuple):
        super().__init__(RequestHandlerClass=handler, server_address=addr)
        self.log = Logger('server_')
        self.request_queue_size = 12
        self.timeout = 1
        self.allow_reuse_address = True
        self.log.info(f"Server started at: {addr}")
        self.started = datetime.now().timestamp()
        self.wl_last_update = datetime.now().timestamp()
        self.wl = get_whitelisted()

    def handle_timeout(self):
        self.wl = get_whitelisted()
        # self.handle_timeout()
        logger.info(f"!in timeout! Userkeys was updated")


    def process_request(self, request, client_address):
        logging.info(f'Connection from: %r', client_address)
        super().process_request(request, client_address)


if __name__ == '__main__':
    with PBStatServer(handler=ReqHandler, addr=app_data.address) as server:
        # server.timeout = 1
        server.handle_timeout()
        server.serve_forever()

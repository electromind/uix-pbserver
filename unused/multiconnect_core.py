#!/usr/bin/env python3

from utils import Logger
import socket
import selectors
import types
import re
import mysql.connector
from utils import get_timestring as t_now

sel = selectors.DefaultSelector()
HOST = '10.0.1.5'
PORT = 2512
logger = Logger('multi')


def get_db():
    conn = mysql.connector.connect(
        user='root',
        password='password',
        database='whitelist',
        host='localhost')
    cur = conn.cursor()
    return conn, cur


def is_valid_key(key: str):
    if key and (len(key) == 32 and re.match(r"^[A-Za-z0-9]*$", key)):
        return True
    else:
        return False


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"{t_now()}accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def auth(key: str):
    userkey = None
    if 'auth_me:' in key:
        userkey = key.replace('auth_me', '')
    if is_valid_key(userkey):
        conndb, cur = get_db()
        cur.execute('''SELECT account_key FROM user_keys''')
        user = cur.fetchone()
        conndb.close()
        if user:
            logger.info(f'Auth - OK: {userkey}')
            return True
        else:
            logger.info(f'Auth - Fail: User: {userkey} is not whitelisted')
            return False

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print(f"{t_now()}closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
        if recv_data and 'auth_me:' in str(recv_data, 'utf-8'):
            if auth(key=str(recv_data, 'utf-8')):
                data.outb = b"True"
            else:
                data.outb = b"False"
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"{t_now()}echoing", repr(data.outb), "to", data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((HOST, PORT))
lsock.listen(128)
print(f"{t_now()}listening on", (HOST, PORT))
lsock.setblocking(False)

sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print(f"{t_now()}caught keyboard interrupt, exiting")
except ConnectionResetError as err:
    pass
finally:
    sel.close()

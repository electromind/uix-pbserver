import socket
import select
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] (%(processName)-10s) (%(threadName)-10s) %(message)s'
)

read_waiters = {}
write_waiters = {}
connections = {}


def accept_handler(serversocket: socket.socket) -> None:
    clientsocket, (client_address, client_port) = serversocket.accept()
    clientsocket.setblocking(False)
    logging.debug(f"New client: {client_address}:{client_port}")
    connections[clientsocket.fileno()] = (clientsocket, client_address, client_port)
    read_waiters[clientsocket.fileno()] = (recv_handler, (clientsocket.fileno(),))
    read_waiters[serversocket.fileno()] = (accept_handler, (serversocket,))


def recv_handler(fileno) -> None:
    def terminate():
        del connections[clientsocket.fileno()]
        clientsocket.close()
        logging.debug(f"Bye-Bye: {client_address}:{client_port}")

    clientsocket, client_address, client_port = connections[fileno]

    try:
        message = clientsocket.recv(1024)
    except OSError:
        terminate()
        return

    if len(message) == 0:
        terminate()
        return

    logging.debug(f"Recv: {message} from {client_address}:{client_port}")
    write_waiters[fileno] = (send_handler, (fileno, message))


def send_handler(fileno, message) -> None:
    clientsocket, client_address, client_port = connections[fileno]
    sent_len = clientsocket.send(message)
    logging.debug("Send: {} to {}:{}".format(message[:sent_len], client_address, client_port))
    if sent_len == len(message):
        read_waiters[clientsocket.fileno()] = (recv_handler, (clientsocket.fileno(),))
    else:
        write_waiters[fileno] = (send_handler, (fileno, message[sent_len:]))


def main(host: str = '10.0.1.5', port: int = 2512) -> None:
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setblocking(False)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    serversocket.bind((host, port))
    serversocket.listen(128)

    read_waiters[serversocket.fileno()] = (accept_handler, (serversocket,))
    while True:
        rlist, wlist, _ = select.select(read_waiters.keys(), write_waiters.keys(), [], 60)

        for r_fileno in rlist:
            handler, args = read_waiters.pop(r_fileno)
            handler(*args)

        for w_fileno in wlist:
            handler, args = write_waiters.pop(w_fileno)
            handler(*args)


if __name__ == "__main__":
    main()

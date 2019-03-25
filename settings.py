#!/usr/bin/env python3
class Settings:
    def __init__(self, debug=True):
        self.__BUFFER_SIZE = 1024
        if debug:
            self.__host = '10.0.1.5'
            self.__port = 2512
        else:
            self.__host = '109.104.178.163'
            self.__port = 2511

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @property
    def address(self):
        return tuple([self.host, self.port])

    @property
    def buff_size(self):
        return self.__BUFFER_SIZE

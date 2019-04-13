#!/usr/bin/env python3
class Settings:
    def __init__(self, debug=False):
        self.__BUFFER_SIZE = 1024
        self.wl_update_interval = 300
        if debug:
            # self.__host = '10.0.1.3'
            # self.__port = 2512
            self.__host = '10.0.1.9'
            self.__port = 2510
        else:
            self.__host = '10.0.1.9'
            self.__port = 2511

    @property
    def host(self):
        return self.__host

    @property
    def port(self):
        return self.__port

    @property
    def address(self):
        return self.host, self.port

    @property
    def buff_size(self):
        return self.__BUFFER_SIZE

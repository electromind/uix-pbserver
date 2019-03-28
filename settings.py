#!/usr/bin/env python3
class Settings:
    def __init__(self, debug=True):
        self.__BUFFER_SIZE = 1024
        self.wl_update_interval = 300
        if debug:
            self.__host = '10.0.1.5'
            self.__port = 2512
        else:
            self.__host = '10.0.1.9'  # '109.104.178.163'
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

# ######## Whitelist Credentials ########
WL_HOST = '209.250.232.25'
WL_USER = 'mrwhite'
WL_PASS = '@e1ectromind'
WL_KEY_FILE_NAME = '/private'
WL_FILE_NAME = 'wl.json'
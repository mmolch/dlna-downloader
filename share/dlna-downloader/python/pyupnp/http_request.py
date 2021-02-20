from .object import Object

from enum import Enum
import httplib2
import logging
import socket
from threading import Thread


class HttpRequest(Object):
    class Event(Object.Event):
        STATE_CHANGED = 1


    class State(Enum):
        INIT = 1
        RUNNING = 2
        FINISHED = 3
        ERROR = 4
        CANCELED = 5


    def __init__(self, method, address, url, headers={}, body='', timeout=60):
        Object.__init__(self)

        self.__method = method
        self.__address = address
        self.__url = url
        self.__headers = headers
        self.__body = body
        self.__timeout = timeout

        self.__cancel = False
        self.__state = self.State.INIT
        self.__response_headers = None
        self.__response_body = None
        self.__error_message = ''

        self.__connection = httplib2.HTTPConnectionWithTimeout(*address, timeout=timeout)


    def Cancel(self):
        self.__cancel = True

        try:
            self.__connection.sock.shutdown(socket.SHUT_WR)
        except:
            pass


    def Request(self):
        if self.state != self.State.INIT:
            return

        self.__SetState(self.State.RUNNING)
        Thread(group=None, target=self.__WorkerThread).start()


    def __WorkerThread(self):
        try:
            self.__connection.request(self.__method, self.__url, self.__body, self.__headers)

            response = self.__connection.getresponse()
            self.__response_headers = response.headers
            self._logger.debug(self.__response_headers)

            self.__response_body = response.read()
            self._logger.debug(self.__response_body)

            self.__SetState(self.State.FINISHED)

        except Exception as e:
            self.__error_message = str(e)
            self._logger.warning(str(e))

            if self.state == self.__cancel:
                self.__SetState(self.State.CANCELED)
            else:
                self.__SetState(self.State.ERROR)


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    def __del__(self):
        try:
            self.__connection.sock.shutdown(socket.SHUT_WR)
        except:
            pass


    @property
    def method(self):
        return self.__method


    @property
    def address(self):
        return self.__address


    @property
    def url(self):
        return self.__url


    @property
    def headers(self):
        return self.__headers


    @property
    def body(self):
        return self.__body


    @property
    def timeout(self):
        return self.__timeout


    @property
    def state(self):
        return self.__state


    @property
    def response_headers(self):
        return self.__response_headers


    @property
    def response_body(self):
        return self.__response_body


    @property
    def error_message(self):
        return self.__error_message

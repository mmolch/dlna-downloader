from pyupnp import Object

from enum import Enum
import os
from threading import Thread
import time
import urllib.request



class Transfer(Object):

    class Event(Object.Event):
        STATE_CHANGED = 1 # callback(source, state)
        UPDATE = 2        # callback(source)


    class State(Enum):
        INIT = 1
        CONNECTING = 2
        TRANSFERING = 3
        FINISHED = 4


    def __init__(self, filename, source, size):
        Object.__init__(self)

        self.__filename = filename
        self.__source = source
        self.__size = size

        self.__state = self.State.INIT
        self.__error_message = None
        self.__received_bytes = 0
        self.__speed = 0
        
        self.__cancel = False
        self.__request = None
        self.__outfile = None
        self.__time = None


    def Reset(self):
        if self.state != self.State.FINISHED:
            return

        self.__state = self.State.INIT
        self.__error_message = None
        self.__received_bytes = 0
        self.__speed = 0
        
        self.__cancel = False
        self.__request = None
        self.__outfile = None
        self.__time = None

        self.__SetState(self.State.INIT)
        


    def Start(self):
        if self.state != self.State.INIT:
            return

        self.__SetState(self.State.CONNECTING)

        Thread(group=None, target=self.__WorkerThread).start()


    def Cancel(self):
        self.__cancel = True


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, self, state)


    def __WorkerThread(self):
        try:
            with urllib.request.urlopen(self.source, timeout=60) as self.__request:
                self.__received_bytes = 0
                speed = 1000000

                if not os.path.exists(os.path.dirname(self.__filename)):
                    os.makedirs(os.path.dirname(self.__filename))

                with open(self.__filename, 'wb') as self.__outfile:
                    self.__time = time.time()
                    perf_counter = time.perf_counter()
                    while not self.__request.isclosed():
                        if self.__cancel:
                            break

                        buffer = self.__request.read(int(speed))
                        self.__SetState(self.State.TRANSFERING)

                        perf_counter_new = time.perf_counter()
                        speed = int(len(buffer)/(perf_counter_new-perf_counter))
                        perf_counter = perf_counter_new

                        self.__outfile.write(buffer)

                        self.__received_bytes += len(buffer)
                        self.__speed = speed

                        self.Emit(self.Event.UPDATE)

        except Exception as e:
            self._logger.info(str(e))
            self.__error_message = str(e)

        self.__SetState(self.State.FINISHED)


    @property
    def filename(self):
        return self.__filename


    @property
    def source(self):
        return self.__source


    @property
    def size(self):
        return self.__size


    @property
    def state(self):
        return self.__state


    @property
    def error_message(self):
        return self.__error_message


    @property
    def received_bytes(self):
        return self.__received_bytes


    @property
    def speed(self):
        return self.received_bytes/self.seconds


    @property
    def seconds(self):
        return int(time.time()-self.__time)+1


    @property
    def canceled(self):
        return self.__cancel

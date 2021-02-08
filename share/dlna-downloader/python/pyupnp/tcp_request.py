from .object import Object

from enum import Enum
import socket
import threading

class TcpRequest(Object):
    """A simple event-base wrapper around a TCP socket

    Properties:
        state : State        # [Read-only]
        address : (str,int)  # The address of the remote device
        request : bytes      # The request packet that is sent to the remote system as bytes
        response : bytes     # The response from the remote device [Read-only]
        timeout : int        # The timeout for the request
        error_message : str  # Contains the error message [Read-only]

    Events:
        STATE_CHANGED  # Sends the current state to bound functions

    States:
        IDLE      # Object created
        STARTED   # Send() called
        WAITING   # Waiting for responses
        CANCELED  # Manually canceled
        SUCCESS  # Successfully finished
        TIMEDOUT  # Connection timed out
        ERROR     # An error occurred (Check error_message)
        CONNECTED # The socket is connected

    Methods:
        Cancel()  # Cancel the running request
        Send()    # Send the request to the remote device

    """

    class Event(Enum):
        STATE_CHANGED = 1


    class State(Enum):
        IDLE = 1
        BUSY = 2
        ERROR = 3
        CANCELED = 4

    def __init__(self, address=None, request=None, timeout=60):
        Object.__init__(self)

        self.__state = self.State.IDLE
        self.__socket = None
        self.__address = address
        self.__timeout = timeout
        self._error_message = None
        self.__request = request
        self.__response = b''
        self.__cancel = False


    def Send(self):
        if self.state == self.State.BUSY:
            return

        self.__SetState(self.State.BUSY)
        self.__cancel = False
        self._error_message = ''

        threading.Thread(group=None, target=self.__WorkerThread).start()


    def Cancel(self):
        if self.__cancel:
            return

        if self.state != self.State.BUSY:
            return

        self.__cancel = True
        try:
            self.__socket.shutdown(socket.SHUT_WR)
        except Exception as e:
            print(str(e))


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    @property
    def state(self):
        return self.__state


    @property
    def timeout(self):
        return self.__timeout


    @timeout.setter
    def timeout(self, timeout):
        if self.__timeout == timeout:
            return

        if self.__state == self.State.BUSY:
            self._logger.debug("Tried to change the timeout while running")
            return

        self.__timeout = timeout

    
    @property
    def address(self):
        return self.__address


    @address.setter
    def address(self, address):
        if self.__address == address:
            return

        if self.__state == self.State.BUSY:
            self._logger.debug("Tried to change the address while running")
            return

        self.__address = address


    @property
    def request(self):
        return self.__request


    @request.setter
    def request(self, request):
        if self.__request == request:
            return

        if self.__state == self.State.BUSY:
            self._logger.debug("Tried to change the request while running")
            return

        self.__request = request


    @property
    def error_message(self):
        return self._error_message

    
    @property
    def response(self):
        return self.__response


    def __str__(self):
        return 'Address:{address}, State:{state}, Timeout:{timeout}, Request:{request}, Response:{response}'.format(address=str(self.address), state=self.state, timeout=self.timeout, request=self.request, response=self.response)


    def __CreateSocket(self):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.settimeout(self.timeout)
            self.__socket.connect(self.address)
            self._logger.debug("CONN:{}".format(self.__address))

        except Exception as e:
            self._logger.info("Failed to connect socket: {}".format(str(e)))
            self._error_message = str(e)
            self.__socket = None
            self.__running = False


    def __WorkerThread(self):
        self.__CreateSocket()
        if not self.__socket:
            self.__SetState(self.State.ERROR)

        else:
            try:
                self._logger.debug("SEND:{}:{}".format(self.__address, self.__request))
                self.__socket.sendall(self.__request)

                while True:
                    data = self.__socket.recv(8192)
                    if self.__cancel:
                        break

                    if not data:
                        break

                    self.__response += data

            except Exception as e:
                self._logger.warning("Failed to read from socket: {}, {}".format(str(self.__address), str(e)))
                self._error_message = str(e)

            finally:
                if self.__response:
                    self._logger.debug("RECV:{}:{}".format(self.__address, self.__response))

                self._logger.debug("CLOS:{}".format(self.__address))
                self.__socket.close()
                self.__socket = None
                self.__running = False

                if self.__cancel:
                    self.__SetState(self.State.CANCELED)
                elif self._error_message:
                    self.__SetState(self.State.ERROR)
                else:
                    self.__SetState(self.State.IDLE)

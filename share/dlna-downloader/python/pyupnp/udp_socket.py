from .object import Object

from enum import Enum
import logging
import socket
from threading import Thread


class UdpSocket(Object):
    """A simple event-driven UDP socket wrapper

    Events:
        STATE_CHANGED = 1 # callback(state)
        RECEIVED_DATA = 2 # callback(data, addr)

    States:
        CONNECTED
        DISCONNECTED

    Properties:
        address : (ip, port) # The broadcast address the server is receiving messages for
        state : State        # The state of the server
        error_message : str  # Error message

    Methods:
        Connect()
        Disconnect()
    """

    class Event(Object.Event):
        STATE_CHANGED = 1
        RECEIVED_DATA = 2


    class State(Enum):
        CONNECTED = 1
        DISCONNECTED = 2


    def __init__(self):
        Object.__init__(self)
        self.__logger = logging.getLogger(self.__class__.__name__)

        self.__local_ip = ''
        self.__error_message = ''
        self.__quit = False
        self.__running = False
        self.__socket = None
        self.__state = self.State.DISCONNECTED


    @property
    def local_ip(self):
        return self.__local_ip


    @local_ip.setter
    def local_ip(self, ip):
        if self.__local_ip == ip:
            return

        if self.__state == self.State.CONNECTED:
            self.__logger.warning("Tried to set a new local ip while running: {}".format(str(ip)))
            return

        self.__local_ip = ip


    def SendPacket(self, packet=b'', to=None):
        if not self.__running or self.__quit:
            return

        if not to:
            to = ('239.255.255.250', 1900)

        try:
            if self.__socket:
                self.__socket.sendto(packet, to)
                self._logger.debug("SEND {}: {}".format(str(to), str(packet)))

        except Exception as e:
            self._logger.warning("Failed to write to socket: {}".format(str(e)))


    def Connect(self):
        if self.__running:
            return

        self.__running = True
        self.__quit = False

        self.__CreateSocket()
        if not self.__socket:
            self.__running = False
            return

        Thread(group=None, target=self.__WorkerThread).start()


    def Disconnect(self):
        if not self.__running or self.__quit:
            return

        self.__quit = True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            target_ip = '127.0.0.1'
            sock_ip, sock_port = self.__socket.getsockname()

            if sock_ip != '0.0.0.0':
                target_ip = sock_ip

            sock.sendto(b'0', (target_ip, sock_port))
            sock.close()

        except Exception as e:
            self._logger.warning("Failed to disconnect socket: {}".format(str(e)))


    def __SetState(self, state):
        if self.__state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    def __CreateSocket(self):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.__socket.bind((self.__local_ip, 0))
            self._logger.debug("Connected: {}".format(self.__socket.getsockname()))
            self.__SetState(self.__SetState(self.State.CONNECTED))
        except Exception as e:
            self._logger.warning("Failed to create socket: {}".format(str(e)))
            self.__socket = None
            self.__running = False


    def __WorkerThread(self):
        try:
            while True:
                data, addr = self.__socket.recvfrom(2048)
                if self.__quit:
                    break

                self._logger.debug("RECV {}: {}".format(str(addr), str(data)))
                self.Emit(self.Event.RECEIVED_DATA, data, addr)

        except Exception as e:
            self._logger.warning("Failed to read from socket: {}".format(str(e)))

        finally:
            self._logger.debug("Disonnected: {}".format(self.__socket.getsockname()))
            self.__socket.close()
            self.__socket = None
            self.__running = False
            self.__SetState(self.State.DISCONNECTED)

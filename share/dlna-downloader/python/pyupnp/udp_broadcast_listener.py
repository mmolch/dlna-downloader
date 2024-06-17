from .object import Object

from enum import Enum
import logging
import socket
from threading import Thread
import struct
import time

class UdpBroadcastListener(Object):
    """A simple event-driven server listening for UDP broadcasts

    Events:
        STATE_CHANGED = 1 # callback(state)
        RECEIVED_DATA = 2 # callback(data, addr)

    States:
        CONNECTED
        DISCONNECTED

    Properties:
        address : (ip, port) # The broadcast address the server is receiving messages for
        local_ip : str        # Bind the socket to this local IP address
        error_message : str  # Error message
        state : State        # The state of the server

    Methods:
        Connect()
        Disconnect()
    """

    class Event(Object.Event):
        STATE_CHANGED = 1 # callback(state)
        RECEIVED_DATA = 2 # callback(data, addr)


    class State(Enum):
        CONNECTED = 1
        DISCONNECTED = 2


    def __init__(self):
        Object.__init__(self)
        self.__logger = logging.getLogger(self.__class__.__name__)

        self.__address = ('239.255.255.250', 1900)
        self.__local_ip = ''
        self.__error_message = ''
        self.__quit = False
        self.__running = False
        self.__socket = None
        self.__state = self.State.DISCONNECTED


    @property
    def address(self):
        return self.__address


    @address.setter
    def address(self, address):
        if self.__address == address:
            return

        if self.__running:
            self.__logger.warning("Tried to set a new address while running: {}".format(str(address)))
            return

        self.__address = address


    @property
    def local_ip(self):
        return self.__local_ip


    @local_ip.setter
    def local_ip(self, ip):
        if self.__local_ip == ip:
            return

        if self.__running:
            self.__logger.warning("Tried to set a new local ip while running: {}".format(str(ip)))
            return

        self.__local_ip = ip


    def __SetState(self, state):
        if self.__state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    def Connect(self):
        if self.__running:
            return

        self.__running = True
        self.__quit = False
        self.__error_message = None
        Thread(group=None, target=self.__Run).start()


    def Disconnect(self):
        if not self.__running:
            return

        self.__quit = True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            target_ip = '239.255.255.250'
            sock_ip, sock_port = self.__socket.getsockname()

            if sock_ip != '0.0.0.0':
                target_ip = sock_ip

            sock.sendto(b'0', (target_ip, sock_port))
            sock.close()

        except Exception as e:
            self.__logger.warning("Failed to disconnect socket: {}".format(str(e)))


    def __Run(self):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            self.__socket.bind((self.__local_ip, self.__address[1]))

            mreq = struct.pack('4sl', socket.inet_aton(self.__address[0]), socket.INADDR_ANY)
            self.__socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            self.__logger.debug("Connected: {}".format(self.__socket.getsockname()))
            self.__SetState(self.State.CONNECTED)

            while True:
                data, addr = self.__socket.recvfrom(2048)
                if self.__quit:
                    break

                if not data:
                    continue

                self.__logger.debug("from {}: {}".format(str(addr), str(data)))
                self.Emit(self.Event.RECEIVED_DATA, data, addr)

        except Exception as e:
                self.__logger.warning(str(e))
                self.__error_message = e

        finally:
            self.__logger.debug("Disonnected: {} {}".format(self.__local_ip, self.__address))
            self.__socket.close()
            self.__socket = None
            self.__running = False
            self.__SetState(self.State.DISCONNECTED)

from .client_device import ClientDevice
from .object import Object
from .udp_broadcast_listener import UdpBroadcastListener
from .udp_socket import UdpSocket
from .util import http_header_to_dict

from enum import Enum
import platform
import threading
import time


class PyUpnp(Object):
    """This class manages the whole PyUpnp system

    Events:
        STATE_CHANGED         # callback(state)
        CLIENT_DEVICE_ADDED   # callback(device)
        CLIENT_DEVICE_REMOVED # callback(device)
        SERVER_DEVICE_ADDED   # callback(device)
        SERVER_DEVICE_REMOVED # callback(device)

    States:
        STOPPED
        RUNNING

    Methods:
        Start()
        Stop()
        RegisterClientDevice(class) # Takes a subclass of ClientDevice
        RegisterServerDevice(class) # Takes a subclass of ServerDevice
        RegisterClientService(class) # Takes a subclass of ClientService
        RegisterServerService(class) # Takes a subclass of ServerService

    Properties:
        xxx

    
    Usage:
        def OnClientDeviceAdded(device):
            content_directory = device.services[ContentDirectoryClientService]
            content_directory.Browse(lambda result: print(str(result)))

        upnp = PyUpnp()
        upnp.RegisterClientService(ContentDirectoryClientService)
        upnp.Bind(upnp.Event.CLIENT_DEVICE_ADDED, OnClientDeviceAdded)
        upnp.Start()
        upnp.Discover()
    """

    class Event(Object.Event):
        STATE_CHANGED = 1
        CLIENT_DEVICE_ADDED = 2
        CLIENT_DEVICE_REMOVED = 3
        SERVER_DEVICE_ADDED = 4
        SERVER_DEVICE_REMOVED = 5


    class State(Enum):
        STOPPED = 1
        RUNNING = 2

    
    def __init__(self, user_agent="PyUpnp", user_agent_version="1.0"):
        Object.__init__(self)

        self.__state = self.State.STOPPED
        self.__running = False

        self._platform_system = platform.system()
        self._platform_release = platform.release()
        self._user_agent = user_agent
        self._user_agent_version = user_agent_version

        self.__search_timeout = 3
        
        self.__client_devices = {}
        self.__client_devices_probe = {}
        self.__server_devices = {}
        self.__client_device_class = ClientDevice
        self.__registered_server_devices = {}
        self.__registered_client_services = {}
        self.__registered_server_services = {}

        self.__broadcast_listener = UdpBroadcastListener()
        self.__broadcast_listener.Bind(UdpBroadcastListener.Event.RECEIVED_DATA, self.__OnBroadcastReceived)

        self.__search_socket = UdpSocket()
        self.__search_socket.Bind(UdpSocket.Event.RECEIVED_DATA, self.__OnSearchResponse)


    @property
    def _registered_client_services(self):
        return self.__registered_client_services


    def Start(self):
        if self.__running:
            return

        self.__running = True
        threading.Thread(group=None, target=self.__TimeoutWorker).start()
        self.__search_socket.Connect()
        self.__broadcast_listener.Connect()


    def Stop(self):
        if not self.__running:
            return

        self.__broadcast_listener.Disconnect()
        self.__search_socket.Disconnect()
        self.__running = False


    def RegisterClientService(self, clientServiceClass):
        if clientServiceClass.URN in self.__registered_client_services:
            return

        self.__registered_client_services[clientServiceClass.URN] = clientServiceClass


    def SetClientDeviceClass(self, _class):
        if self.__client_device_class == _class:
            return

        if _class == None:
            self.__client_device_class = ClientDevice
            return

        self.__client_device_class = _class


    def __OnBroadcastReceived(self, broadcast_listener, data, addr):
        http_header = http_header_to_dict(data)
        if not http_header:
            return

        if 'MAN' in http_header and http_header['MAN'] == '"ssdp:discover"':
            self.__OnSsdpDiscover(http_header, addr)

        elif 'LOCATION' in http_header:
            self.__OnNotify(http_header, addr)

        else:
            self._logger.debug('Unhandled broadcast')


    def __OnSsdpDiscover(self, header, addr):
        self._logger.debug('__OnSsdpDiscover')

        for device in self.__server_devices:
            # device.RespondToSsdpDiscover(header, addr)
            pass


    def __OnNotify(self, header, addr):
        self._logger.debug('__OnNotify')
        nts = header['NTS'] if 'NTS' in header else None

        if not 'NT' in header:
            return

        if nts == 'ssdp:alive':
            if not 'NT' in header:
                return

            self.__HandleAliveDevice(header, addr, header['NT'])

        elif nts == "ssdp:byebye":
            location = header['LOCATION']
            if location in self.__client_devices:
                device = self.__client_devices[location]
                self.__RemoveDevice(location)


    def __TimeoutWorker(self):
        "Counts the timeout of devices down and removes devices on timeout"

        time_prev = time.time()
        while self.__running:
            time_curr = time.time()
            delta_time = round(time_curr - time_prev)
            time_prev = time_curr
            try:
                for device in self.__client_devices.values():

                    device._timeout -= delta_time

                    if device._timeout == 0:
                        self.__RemoveDevice(device.location)

                    maxage_half = int(device._maxage/2)
                    if device._timeout <= maxage_half:
                        device._maxage = device._timeout
                        if device._maxage >= 300:                    
                            self.Discover('uuid:{}'.format(device.uuid))
            except:
                pass

            time.sleep(1)
           

    def __RemoveDevice(self, location):
        device = self.__client_devices[location]
        self.__client_devices.pop(location)
        device._CleanUp()
        self.Emit(self.Event.CLIENT_DEVICE_REMOVED, device)


    def _GetClientServiceClass(self, urn):
        if not urn:
            return None

        # Direct match of urn+version
        if urn in self.__registered_client_services:
            return self.__registered_client_services[urn]

        # Have higher urn versions handled by the next lower registered version
        try:
            urn_fmt, urn_version = urn.rsplit(':', 1)
            urn_version = int(urn_version)
            urn_fmt = "{}:{{}}".format(urn_fmt)
        except:
            return None

        for i in range(urn_version-1, 0, -1):
            _urn = urn_fmt.format(i)
            if _urn in self.__registered_client_services:
                return self.__registered_client_services[_urn]
        
        return None


    # Discover ####################################################################################
    def Discover(self, search_target='ssdp:all', address=None):
        packet = self._CreateSearchPacket(search_target)
        self.__search_socket.SendPacket(packet, address)


    def DiscoverRegisteredClientServices(self):
        for urn in self.__registered_client_services.keys():
            self.Discover(urn)


    def _CreateSearchPacket(self, search_target='ssdp:all'):
        packet = "\r\n".join([
            'M-SEARCH * HTTP/1.1',
            'User-Agent: {}/{} UPnP/1.0 {}/{}'.format(self._platform_system, self._platform_release, self._user_agent, self._user_agent_version),
            'HOST: 239.255.255.250:1900',
            'Accept: */*',
            'MAN: "ssdp:discover"',
            'ST: {}'.format(search_target),
            'MX: {}'.format(self.__search_timeout),
            '',
            ''
            ])

        packet = packet.encode('utf-8')
        return packet


    def __OnSearchResponse(self, udp_socket, data, addr):
        http_header = http_header_to_dict(data)
        if not http_header:
            return

        if not 'LOCATION' in http_header:
            return

        if not 'ST' in http_header:
            return

        self.__HandleAliveDevice(http_header, addr, http_header['ST'])

        
    def __HandleAliveDevice(self, header, addr, urn):
        location = header['LOCATION']

        if location in self.__client_devices:
            try:
                device = self.__client_devices[location]
                if not device:
                    return

                maxage = int(header['CACHE-CONTROL'].split('=')[1])

                device._maxage = maxage
                device._timeout = maxage

            except Exception as e:
                self._logger.debug('{}'.format(str(e)))

        else:
            if self._GetClientServiceClass(urn):
                # test for ip, name, searchTarget...

                threading.Thread(group=None, target=self.__ProbeDevice, args=(header, addr, location)).start()


    def __ProbeDevice(self, header, addr, location):
        
        self.__client_devices_probe[location] = None
        device = self.__client_device_class(self, header, addr)
        if device._initialized:
            self.__client_devices[location] = device
            self.Emit(self.Event.CLIENT_DEVICE_ADDED, device)

        self.__client_devices_probe.pop(location)


    @property
    def client_devices(self):
        return self.__client_devices

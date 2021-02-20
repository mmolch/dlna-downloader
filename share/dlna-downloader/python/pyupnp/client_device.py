from .object import Object
from .util import *
#import upnp.upnp_util as upnp_util
#from upnp.content_directory_service import ContentDirectoryService

from urllib.request import urlopen
import os
from xml.etree import ElementTree


class ClientDevice(Object):
    """This class represents a client upnp device

    Properties:
        ip          # The IP of the device
        port        # The port the device listens on
        timeout     # Time in seconds until the device will be automatically removed
        description # The device description xml
        name        # The friendlyName of the device
        services    # A dict containing the provided services
        userdata    # A dict that can be freely used by the user
    """
    def __init__(self, pyupnp, http_header, addr):
        Object.__init__(self)

        self._logger.info('Initializing...')

        self._initialized = False
        self.__services = {}
        self.userdata = {}


        # Required
        try:
            self.__location = http_header['LOCATION']
            self._logger.debug('LOCATION: {}'.format(self.__location))
            self.__ip = host_from_url(self.location)
            self.__port = port_from_url(self.location)
            self._maxage = int(http_header['CACHE-CONTROL'].split('=')[1])
            self._timeout = self._maxage
            self.__usn = http_header['USN']
            self._logger.debug('USN: {}'.format(self.__usn))
            self.__uuid = self.usn.split(':')[1]

        except KeyError as e:
            self._logger.warning('KeyError: Not in http_header: ' + str(e))
            return

        self.__location_dir = os.path.dirname(path_from_url(self.location))


        # Required
        try:
            raw_desc_xml = urlopen(self.location, timeout=3).read()
            self.__description = ElementTree.fromstring(raw_desc_xml)

        except Exception as e:
            self._logger.warning('Failed to retrieve device decription: ' + str(e))
            return


        # Required
        try:
            self.__name = self.FindInDescription('d:device/d:friendlyName').text
            self._logger.info('Found ' + self.name)

        except Exception as e:
            self._logger.warning('Failed to retrieve friendly name: ' + str(e))
            return


        try:
            services = self.FindInDescription('d:device/d:serviceList').getchildren()
            for service in services:
                try:
                    serviceType = self.FindInDescription('d:serviceType', service).text
                    ServiceClass = pyupnp._GetClientServiceClass(serviceType)
                    if ServiceClass:
                        newService = ServiceClass(pyupnp, self, service)
                        if newService._initialized:
                            self.__services[ServiceClass] = newService

                except Exception as e:
                    self._logger.warning("Failed to create service: {}".format(str(e)))
                    return

        except Exception as e:
            self._logger.error(str(e))
            return


        self._initialized = True


    def _CleanUp(self):
        "This method is called after it has been removed from the upnp system"
        pass


    def FindInDescription(self, path, elementTree=None):
        if not elementTree:
            elementTree = self.__description

        try:
            namespaces = {}
            namespaces['d'] = "urn:schemas-upnp-org:device-1-0"
            return elementTree.find(path, namespaces)

        except Exception as e:
            self._logger.warning("Not found in description: {}".format(str(e)))
            return None


    def path_to_url(self, path):
        if path.startswith("http://"):
            return path

        if not path.startswith('/'):
            path = "{dir}/{path}".format(dir=self.__location_dir, path=path)

        return "http://{ip}:{port}{path}".format(ip=self.ip, port=self.port, path=path)


    @property
    def location(self):
        return self.__location


    @property
    def ip(self):
        return self.__ip

    
    @property
    def port(self):
        return self.__port


    @property
    def usn(self):
        return self.__usn


    @property
    def uuid(self):
        return self.__uuid


    @property
    def description(self):
        return self.__description


    @property
    def name(self):
        return self.__name


    @property
    def services(self):
        return self.__services


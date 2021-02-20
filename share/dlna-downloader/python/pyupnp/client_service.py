from .object import Object

class ClientService(Object):

    URN = 'upnp:rootdevice'

    class Event(Object.Event):
        pass

    
    def __init__(self, pyupnp, device, description):
        Object.__init__(self)
        self._logger.info("{}:Initializing...".format(device.name))

        self._initialized = False
        self.__upnp = pyupnp
        self.__device = device
        self.__description = description
        self.userdata = {}


        # All fields are required by the UPNP specification
        try:
            self.__service_id = device.path_to_url(device.FindInDescription('d:serviceId', description).text)
            self._logger.debug('serviceID: {}'.format(self.__service_id))
            self.__scpd_url =  device.path_to_url(device.FindInDescription('d:SCPDURL', description).text)
            self._logger.debug('SCPDURL: {}'.format(self.__scpd_url))
            self.__contol_url =  device.path_to_url(device.FindInDescription('d:controlURL', description).text)
            self._logger.debug('controlURL: {}'.format(self.__contol_url))
            self.__event_sub_url =  device.path_to_url(device.FindInDescription('d:eventSubURL', description).text)
            self._logger.debug('eventSubURL: {}'.format(self.__event_sub_url))
            
        except Exception as e:
            self._logger.warning("Failed to create service: {}".format(str(e)))
            return


        self._initialized = True


    def _CleanUp(self):
        "This method is called after it has been removed from the upnp system"
        pass


    @property
    def control_url(self):
        try:
            return self.__contol_url
        except:
            return None


    @property
    def scpd_url(self):
        try:
            return self.__scpd_url
        except:
            return None


    @property
    def event_sub_url(self):
        try:
            return self.__event_sub_url
        except:
            return None


    @property
    def device(self):
        return self.__device


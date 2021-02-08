from .object import Object
from .tcp_request import TcpRequest
from .util import path_from_url, host_from_url, port_from_url


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
            self.__scpd_url =  device.path_to_url(device.FindInDescription('d:SCPDURL', description).text)
            self.__contol_url =  device.path_to_url(device.FindInDescription('d:controlURL', description).text)
            self.__event_sub_url =  device.path_to_url(device.FindInDescription('d:eventSubURL', description).text)
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


    def _CreateControlPacket(self, action, envelope):
        packet = "\r\n".join([
                'POST {} HTTP/1.0'.format(path_from_url(self.control_url)),
                'User-Agent: {}/{}'.format('UPNP', '1.0'),
                'Accept: */*',
                'Content-Type: text/xml; charset="utf-8"',
                'HOST: {}:{}'.format(self.device.ip, self.device.port),
                'Content-Length: {}'.format(len(envelope)),
                'SOAPACTION: "{}#{}"'.format(self.URN, action),
                'Connection: close',
                '',
                envelope
            ])

        packet = packet.encode('utf-8')

        self._logger.debug(packet)
        return packet


    def _CreateEnvelope(self, action, data):
        fields = ''
        first = True
        for tag, value in data.items():
            if first:
                first = False
            else:
                fields += '\n'

            fields += '            <{tag}>{value}</{tag}>'.format(tag=tag, value=value)

        envelope = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:{action} xmlns:u="{urn}">
{fields}
        </u:{action}>
    </s:Body>
</s:Envelope>""".format(action=action, urn=self.URN, fields=fields)

        return envelope

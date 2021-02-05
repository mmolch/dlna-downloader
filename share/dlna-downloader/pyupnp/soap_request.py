from .tcp_request import TcpRequest

from xml.etree import ElementTree

class SoapRequest(TcpRequest):
    def __init__(self, *args, **kwargs):
        TcpRequest.__init__(self, *args, **kwargs)

    
    @property
    def soap_response(self):
        if not self.response:
            return None

        if self.error_message:
            return None

        try:
            xml = self.response.split(b'\r\n\r\n', 1)[1].decode('utf-8')
            self._logger.debug(xml)
            doc = ElementTree.fromstring(xml)
            namespaces = {}
            namespaces['s'] = "http://schemas.xmlsoap.org/soap/envelope/"
            namespaces['u'] = "urn:schemas-upnp-org:control-1-0"
            body = doc.find('s:Body', namespaces)

            fault =  body.find('s:Fault', namespaces)
            if not fault:
                return body

            try:
                self._error_message = fault.find('detail/u:UPnPError/u:errorDescription', namespaces).text
            except:
                self._error_message = "Failed to decode error message"
            
            return None

        except Exception as e:
            self._logger.warning("Failed to decode SOAP response: {}".format(str(e)))
            self._error_message = str(e)
            return None

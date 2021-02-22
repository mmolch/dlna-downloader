from.http_request import HttpRequest
from .object import Object

from enum import Enum
import html.parser
import logging
import sys
from xml.etree import ElementTree


class SoapRequest(Object):
    class Event(Object.Event):
        STATE_CHANGED = 1


    class State(Enum):
        INIT = 1
        RUNNING = 2
        FINISHED = 3
        ERROR = 4
        CANCELED = 5


    def __init__(self, address, url, urn, action, data, timeout=60):
        Object.__init__(self)

        self.__state = self.State.INIT
        self.__error_message = ''
        self.__soap_body = None
        
        self.__envelope = self.__CreateEnvelope(urn, action, data)
        self.__headers = {
            'CONTENT-TYPE' : 'text/xml; charset="utf-8"',
            'SOAPACTION' : '"{}#{}"'.format(urn, action),
        }

        self.__http_request = HttpRequest('POST', address, url, self.__headers, self.__envelope, timeout)
        self.__http_request.Bind(HttpRequest.Event.STATE_CHANGED, self.__OnHttpRequestStateChanged)


    def __OnHttpRequestStateChanged(self, state):
        if state == HttpRequest.State.INIT:
            self.__SetState(self.State.INIT)
            return
        elif state == HttpRequest.State.RUNNING:
            self.__SetState(self.State.RUNNING)
            return
        elif state == HttpRequest.State.ERROR:
            self.__error_message = self.__http_request.error_message
            self.__SetState(self.State.ERROR)
            return
        elif state == HttpRequest.State.CANCELED:
            self.__SetState(self.State.CANCELED)
            return

        try:
            doc = ElementTree.fromstring(self.__http_request.response_body)

            namespaces = {}
            namespaces['s'] = "http://schemas.xmlsoap.org/soap/envelope/"
            namespaces['u'] = "urn:schemas-upnp-org:control-1-0"
            self.__soap_body = doc.find('s:Body', namespaces)
            if logging.root.level == logging.DEBUG:
                self._logger.debug('RECV:{}'.format(ElementTree.tostring(self.__soap_body)))

            fault =  self.__soap_body.find('s:Fault', namespaces)
            if fault != None:
                try:
                    self.__error_message = fault.find('detail/u:UPnPError/u:errorDescription', namespaces).text
                except:
                    self.__error_message = "Failed to decode error message"

                self._logger.warning(self.__error_message)
                self.__SetState(self.State.ERROR)
                return

            self.__SetState(self.State.FINISHED)

        
        except Exception as e:
            self.__error_message = str(e)
            self._logger.warning(e)
            self.__SetState(self.State.ERROR)


    def Cancel(self):
        self.__http_request.Cancel()


    def Request(self):
        self.__http_request.Request()


    def __CreateEnvelope(self, urn, action, data):
        fields = ''
        first = True
        for tag, value in data.items():
            if first:
                first = False
            else:
                fields += '\n'

            fields += '<{tag}>{value}</{tag}>'.format(tag=tag, value=value)

        envelope = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:{action} xmlns:u="{urn}">
{fields}
</u:{action}>
</s:Body>
</s:Envelope>

""".format(action=action, urn=urn, fields=fields)

        return envelope


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    @property
    def state(self):
        return self.__state


    @property
    def error_message(self):
        return self.__error_message


    @property
    def soap_body(self):
        return self.__soap_body

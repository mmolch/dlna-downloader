import wx

from pyupnp import Object
from pyupnp.services.content_directory_1_client_service import ContentDirectory1ClientService
from pyupnp import SoapRequest, PyUpnp

from xml.etree import ElementTree
from enum import Enum, IntEnum



class ContentDirectory(Object):
    """This class store information about a directory and retrieves its index"""

    class Event(Object.Event):
        OBJECT_ID_CHANGED = 1
        DEVICE_CHANGED = 2
        STATE_CHANGED = 3
        GOT_MORE_ITEMS = 4


    class State(Enum):
        CONNECTING = 3
        DOWNLOADING = 4
        IDLE = 5
        ERROR = 6


    class Field(Enum):
        TITLE = 0
        TYPE = 1
        ID = 2
        PARENT_ID = 3
        DATE = 4
        CHANNEL = 5
        RES = 6
        DURATION = 7
        SIZE = 8
        MIMETYPE = 9


    class ItemType(IntEnum):
        CONTAINER = 0
        ITEM = 1
        VIDEO = 2
        AUDIO = 3
        PICTURE = 4


    class Statistic(Enum):
        SIZE_OVERALL = 1
        NUM_CONTAINERS = 2
        NUM_ITEMS = 3


    def __init__(self):
        Object.__init__(self)

        self.__state = self.State.IDLE

        # For breadcrumbs / hierarchy
        self.__id_parent_id_map = {} # {id:parent_id}
        self.__id_title_map = {} # {id:title}

        self.__items_total = 0
        self.__items = []
        self.__fields = [] # A list of used fields, used to determine which columns to show
        self.__object_id = "0"
        self.__device = None
        self.__browse_request = None
        self.__error_message = None
        self.__statistics = {}

        wx.GetApp().upnp.Bind(PyUpnp.Event.CLIENT_DEVICE_REMOVED, self.__OnDeviceRemoved)


    def __OnDeviceRemoved(self, device):
        if self.__device == device:
            self.SetDevice(None)


    @property
    def statistics(self):
        return self.__statistics


    @property
    def error_message(self):
        return self.__error_message


    @property
    def fields(self):
        return self.__fields


    @property
    def items_total(self):
        return self.__items_total


    @property
    def items(self):
        return self.__items


    @property
    def device(self):
        return self.__device


    def SetDevice(self, device):
        if self.__device == device:
            return

        self.__items_total = 0
        self.__items = []
        self.__fields = [] # A list of used fields, used to determine which columns to show
        self.__object_id = "0"
        self.__statistics = {}
        self.__device = device
        if self.__browse_request:
            self.__browse_request.Cancel()

        self.__browse_request = None
        self.__error_message = None
        self.Emit(self.Event.DEVICE_CHANGED, device)


    @property
    def object_id(self):
        return self.__object_id


    def SetObjectId(self, object_id="0"):
        if self.__object_id == object_id:
            return

        if self.__browse_request:
            self.__browse_request.Cancel()

        self.__items_total = 0
        self.__items = []
        self.__fields = [] # A list of used fields, used to determine which columns to show
        self.__object_id = object_id
        self.__statistics = {}
        self.__browse_request = None
        self.__error_message = None

        self.Emit(self.Event.OBJECT_ID_CHANGED, object_id)


    def Cancel(self):
        if self.__browse_request:
            self.__browse_request.Cancel()


    @property
    def state(self):
        return self.__state


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    def Load(self):
        if not self.device:
            return

        if self.__browse_request:
            self.__browse_request.Cancel()


        self.__items = []
        self.__fields = []
        self.__items_total = 0

        self.__statistics = {}
        self.__statistics[self.Statistic.NUM_CONTAINERS] = 0
        self.__statistics[self.Statistic.NUM_ITEMS] = 0
        self.__statistics[self.Statistic.SIZE_OVERALL] = 0

        service = self.device.services[ContentDirectory1ClientService]
        self.__browse_request = service.BrowseRequest(object_id=self.object_id)
        self.__browse_request.Bind(SoapRequest.Event.STATE_CHANGED, self.__OnRequestStateChanged)
        self.__SetState(self.State.CONNECTING)
        self.__browse_request.Send()        


    def __OnRequestStateChanged(self, state):
        if state == SoapRequest.State.CANCELED:
            self.__SetState(self.State.IDLE)
        elif state == SoapRequest.State.ERROR:
            self.__error_message = self.__browse_request._error_message
            self.__SetState(self.State.ERROR)
        elif state == SoapRequest.State.BUSY:
            return
        elif state == SoapRequest.State.IDLE:
            response = self.__browse_request.soap_response
            if not response:
                self.__error_message = self.__browse_request._error_message
                self.__SetState(self.State.ERROR)
                return

            namespaces = {}
            namespaces['dc'] = "http://purl.org/dc/elements/1.1/"
            namespaces['u'] = "urn:schemas-upnp-org:service:ContentDirectory:1"
            namespaces['didl'] = 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'
            namespaces['upnp'] = 'urn:schemas-upnp-org:metadata-1-0/upnp/'

            try:
                self.__items_total = int(response.find('u:BrowseResponse/TotalMatches', namespaces).text)
                number_returned = int(response.find('u:BrowseResponse/NumberReturned', namespaces).text)
                if number_returned == 0:
                    self.__SetState(self.State.IDLE)
                    return


                results = ElementTree.fromstring(response.find('u:BrowseResponse/Result', namespaces).text)
                for result in results:
                    item = {}

                    title = result.find('dc:title', namespaces).text
                    item[self.Field.TITLE] = title
                    self.__fields.append(self.Field.TITLE)

                    type = result.tag.rsplit('}').pop()
                    if type == 'container':
                        item[self.Field.TYPE] = self.ItemType.CONTAINER
                        id = result.get('id')
                        parent_id = result.get('parentID')

                        self.__id_title_map[id] = title
                        self.__id_parent_id_map[id] = parent_id

                        item[self.Field.ID] = id
                        item[self.Field.PARENT_ID] = parent_id

                        self.__items.append(item)
                        self.__statistics[self.Statistic.NUM_CONTAINERS] += 1
                        continue

                    item[self.Field.TYPE] = self.ItemType.ITEM

                    try:
                        date = result.find('dc:date', namespaces).text
                        item[self.Field.DATE] = date.replace('T', ' ').rsplit(':', 1)[0]
                        self.__fields.append(self.Field.DATE)
                    except:
                        pass

                    try:
                        item[self.Field.CHANNEL] = result.find('upnp:channelName', namespaces).text
                        self.__fields.append(self.Field.CHANNEL)
                    except:
                        pass

                    try:
                        res = result.find('didl:res', namespaces)
                        item[self.Field.RES] = res.text
                        self.__fields.append(self.Field.RES)

                        try:
                            duration = res.get('duration')
                            if int(duration.replace(':','')) != 0:
                                item[self.Field.DURATION] = duration
                                self.__fields.append(self.Field.DURATION)
                        except:
                            pass

                        try:
                            size = int(res.get('size'))
                            self.__statistics[self.Statistic.SIZE_OVERALL] += size
                            item[self.Field.SIZE] = size
                            self.__fields.append(self.Field.SIZE)                            
                        except:
                            pass

                        try:
                            protocol_info = res.get('protocolInfo')
                            if 'video' in protocol_info:
                                item[self.Field.TYPE] = self.ItemType.VIDEO
                            elif 'audio' in protocol_info:
                                item[self.Field.TYPE] = self.ItemType.AUDIO
                            elif 'image' in protocol_info:
                                item[self.Field.TYPE] = self.ItemType.PICTURE

                            mimetype = protocol_info.split(':')[2]
                            item[self.Field.MIMETYPE] = mimetype
                        except:
                            pass

                    except:
                        pass


                    self.__items.append(item)
                    self.__statistics[self.Statistic.NUM_ITEMS] += 1

            except Exception as e:
                self._logger.warning(str(e))
                self.__error_message = str(e)
                self.__SetState(self.State.ERROR)
                return


            if len(self.__items) < self.__items_total:
                service = self.device.services[ContentDirectory1ClientService]
                self.__browse_request = service.BrowseRequest(starting_index=len(self.items), object_id=self.object_id)
                self.__browse_request.Bind(SoapRequest.Event.STATE_CHANGED, self.__OnRequestStateChanged)
                self.__SetState(self.State.DOWNLOADING)
                self.Emit(self.Event.GOT_MORE_ITEMS)
                self.__browse_request.Send()
            else:
                self.__SetState(self.State.IDLE)


    def GetHierarchy(self):
        "Returns a list of (id:title) tuples"
        try:
            path = []
            curr_id = self.object_id
            while curr_id in self.__id_parent_id_map:
                parent_id = self.__id_parent_id_map[curr_id]
                title = self.__id_title_map[curr_id]
                path.append((curr_id, title))
                curr_id = parent_id

            path.append(("0", self.__device.name))            
            path.reverse()
            return path
        except:
            return {}


    def GetField(self, item, field):
        if field == self.Field.SIZE:
            try:
                return self.__items[item][field]
            except:
                return -1

        try:
            return self.__items[item][field]
        except:
            return ''

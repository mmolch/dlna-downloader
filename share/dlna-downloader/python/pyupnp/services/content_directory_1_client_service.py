from ..client_service import ClientService
from ..soap_request import SoapRequest
from ..util import path_from_url, host_from_url, port_from_url


class ContentDirectory1ClientService(ClientService):

    URN = "urn:schemas-upnp-org:service:ContentDirectory:1"


    def __init__(self, pyupnp, device, description):
        ClientService.__init__(self, pyupnp, device, description)


    def BrowseRequest(self, starting_index=0, requested_count=1024, object_id="0", browse_flag="BrowseDirectChildren", filter="*", sort_criteria=""):
        data = {}
        data['ObjectID'] = object_id
        data['BrowseFlag'] = browse_flag
        data['Filter'] = filter
        data['StartingIndex'] = starting_index
        data['RequestedCount'] = requested_count
        data['SortCriteria'] = sort_criteria

        return SoapRequest((host_from_url(self.control_url), port_from_url(self.control_url)), path_from_url(self.control_url), self.URN, 'Browse', data)

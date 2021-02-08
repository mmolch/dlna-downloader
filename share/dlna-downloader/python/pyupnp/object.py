from enum import Enum
import logging

class Object:
    """The base class for all pyupnp classes, providing simple event handling

    Methods:
        Bind(event, callback)
        UnBind(event, callback)
        Emit(event, *args)
    """
    class Event(Enum):
        pass


    def __init__(self):
        self.__event_callbacks = {}
        for event in self.Event:
            self.__event_callbacks[event] = []

        self._logger = logging.getLogger(self.__class__.__name__)


    def Bind(self, event, callback):
        """Bind the callback to an event

        Usage:
            dev OnEvent(data1, data2, etc):
                pass

            obj.Bind(obj.Event.MY_EVENT, onEvent, data1, data2, etc)
        """
        if callback not in self.__event_callbacks[event]:
            self.__event_callbacks[event].append(callback)


    def UnBind(self, event, callback):
        """Removes a callback from the callback list"""
        if callback in self.__event_callbacks[event]:
            self.__event_callbacks[event].remove(callback)


    def Emit(self, event, *args):
        """Calls all callbacks that are bound to the event"""
        for callback in self.__event_callbacks[event]:
            if not callback:
                self.__event_callbacks[event].remove(callback)
                continue

            callback(*args)

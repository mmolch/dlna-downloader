import wx

from pyupnp.object import Object

from .transfer import Transfer

from enum import Enum

class Transfers(Object):
    class Event(Enum):
        ADDED = 1
        REMOVED = 2
        STATE_CHANGED = 3


    class State(Enum):
        IDLE = 1
        RUNNING = 2


    def __init__(self):
        Object.__init__(self)

        self.__state = self.State.IDLE
        self.__transfers = []

        self.__completed = 0


    def __OnTransferStateChanged(self, source, state):
        if state == Transfer.State.CONNECTING or state == Transfer.State.TRANSFERING:
            self.__SetState(self.State.RUNNING)
        else:
            self.__SetState(self.State.IDLE)

        if state == Transfer.State.FINISHED:
            if not source.error_message:
                if not source.canceled:
                    self.Remove(source)
                    self.__completed += 1
                    self.Start()


    def Start(self):
        if len(self.transfers) > 0:
            self.transfers[0].Bind(Transfer.Event.STATE_CHANGED, self.__OnTransferStateChanged)
            self.transfers[0].Reset()
            self.transfers[0].Start()


    def Stop(self):
        if len(self.transfers) > 0:
            self.transfers[0].Cancel()


    def Add(self, transfer):
        if transfer in self.__transfers:
            return

        self.__transfers.append(transfer)
        self.Emit(self.Event.ADDED, transfer)
        if len(self.transfers) == 1:
            self.Start()


    def Remove(self, transfer):
        if transfer.state == Transfer.State.INIT or transfer.state == Transfer.State.FINISHED:
            self.__transfers.remove(transfer)
        elif transfer.state == Transfer.State.CONNECTING or transfer.state == Transfer.State.TRANSFERING:
            transfer.Cancel()
            self.__transfers.remove(transfer)
        else:
            pass

        self.Emit(self.Event.REMOVED, transfer)


    def __SetState(self, state):
        if self.state == state:
            return

        self.__state = state
        self.Emit(self.Event.STATE_CHANGED, state)


    def GetTransfer(self, index):
        try:
            return self.__transfers[index]
        except:
            return None


    @property
    def transfers(self):
        return self.__transfers


    @property
    def state(self):
        return self.__state


    @property
    def completed(self):
        return self.__completed


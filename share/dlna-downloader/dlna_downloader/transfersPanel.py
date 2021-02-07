import wx

from .transfer import Transfer
from .transfers import Transfers
from .util import SizeToString, SecondsToString

from enum import IntEnum
import os
from threading import Thread
from time import sleep

import gettext
_ = gettext.gettext

class TransfersListView(wx.ListView):
    class Column(IntEnum):
        FILE = 0
        SOURCE = 1
        STATUS = 2


    def __init__(self, parent, *args, **kwargs):
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VIRTUAL|wx.NO_BORDER|wx.LC_SINGLE_SEL, *args, **kwargs)

        self.SetMinSize((400, 150))
        self.EnableAlternateRowColours()
        self.Select(-1, False)

        self.InsertColumn(TransfersListView.Column.FILE, _("File"))
        self.InsertColumn(TransfersListView.Column.SOURCE, _("Source"))
        self.InsertColumn(TransfersListView.Column.STATUS, _("Status"))

        app = wx.GetApp()
        app.transfers.Bind(Transfers.Event.ADDED, lambda transfer: wx.CallAfter(self.OnTransferAdded, transfer))
        app.transfers.Bind(Transfers.Event.REMOVED, lambda transfer: wx.CallAfter(self.OnTransferRemoved, transfer))
        app.transfers.Bind(Transfers.Event.STATE_CHANGED, lambda state: wx.CallAfter(self.OnStateChanged, state))

        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__OnSelectionChanged)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.__OnSelectionChanged)
        self.Bind(wx.EVT_LIST_CACHE_HINT, self.__OnSelectionChanged)


    def __OnSelectionChanged(self, __event):
        if self.GetSelectedItemCount() == 0:
            self.GetParent().button_remove.Disable()
        else:
            self.GetParent().button_remove.Enable()


    def OnResize(self, event):
        self.SetColumnWidth(0, self.GetVirtualSize().width*0.4)
        self.SetColumnWidth(1, self.GetVirtualSize().width*0.4)
        self.SetColumnWidth(2, self.GetVirtualSize().width*0.2)
        self.Layout()
        self.SetColumnWidth(2, self.GetVirtualSize().width*0.2-1)
        self.Layout()
        event.Skip()


    def OnTransferAdded(self, transfer):
        self.SetItemCount(len(wx.GetApp().transfers.transfers))

        self.__OnSelectionChanged(None)


    def OnTransferRemoved(self, transfer):
        self.SetItemCount(len(wx.GetApp().transfers.transfers))

        self.__OnSelectionChanged(None)


    def OnStateChanged(self, state):
        if state == Transfers.State.IDLE:
            if len(wx.GetApp().transfers.transfers) > 0:
                self.GetParent().button_stop.SetLabel(_("Start"))
                self.GetParent().button_stop.Enable()
            else:
                self.GetParent().button_stop.SetLabel(_("Stop"))
                self.GetParent().button_stop.Disable()
        elif state == Transfers.State.RUNNING:
            self.GetParent().button_stop.SetLabel(_("Stop"))
            self.GetParent().button_stop.Enable()
            Thread(group=None, target=self.__UpdateThread).start()

    
    def OnGetItemText(self, item, column):
        if column == 0:
            return os.path.basename(wx.GetApp().transfers.GetTransfer(item).filename)
        elif column == 1:
            return wx.GetApp().transfers.GetTransfer(item).source
        elif column == 2:
            return self.StatusText(item, column)
        elif column == 3:
            return ''
        

    #def OnGetItemImage(self, item):
        #print('OnGetItemImage')
    #    return -1


    def __UpdateThread(self):
        while wx.GetApp().transfers.state == Transfers.State.RUNNING:
            wx.CallAfter(self.Refresh)
            sleep(1)

        wx.CallAfter(self.Refresh)


    def OnGetItemColumnImage(self, item, column):
        #if column == TransfersListView.Column.REMOVE:
        #    return 0
        #else:
        return -1



    def StatusText(self, item, column):
        transfer = wx.GetApp().transfers.GetTransfer(item)
        if not transfer:
            return ''

        if transfer.state == Transfer.State.CONNECTING:
            return _("Connecting…")
        if transfer.state == Transfer.State.TRANSFERING:
            received_str = SizeToString(transfer.received_bytes)
            speed_str = SizeToString(transfer.speed)
            if transfer.size and transfer.size > 0:
                percent_str = str(round(transfer.received_bytes*100/transfer.size, 2))
                remaining_time = SecondsToString(int((transfer.size-transfer.received_bytes)/transfer.speed))
                return "{} %, {}, {}/s, {} {}".format(percent_str, received_str, speed_str, remaining_time, _("remaining"))
            else:
                return "{}, {}/s".format(received_str, speed_str)
        elif transfer.state == Transfer.State.INIT:
            return _("Queued")
        elif transfer.state == Transfer.State.FINISHED:
            if transfer.error_message:
                return transfer.error_message
            else:
                if transfer.canceled:
                    return _("Stopped")
                else:
                    return _("Done")


class TransfersPanel(wx.Control):
    def __init__(self, *args, **kwargs):
        wx.Control.__init__(self, *args, **kwargs)

        sizer1 = wx.BoxSizer(wx.VERTICAL)

        sizer_header = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header.Add(6, 0)
        self.title = wx.StaticText(self, wx.ID_ANY)
        sizer_header.Add(self.title, 0, wx.CENTER)
        sizer_header.Add(6, 0, 1)
        self.button_stop = wx.Button(self, wx.ID_DELETE, label=_('Start'))
        self.button_stop.Disable()
        self.button_stop.Bind(wx.EVT_BUTTON, self.__OnStopButtonClicked)
        sizer_header.Add(self.button_stop)
        sizer_header.Add(3, 0, 0)
        self.button_remove = wx.Button(self, wx.ID_DELETE, label=_('Remove'))
        self.button_remove.Disable()
        self.button_remove.Bind(wx.EVT_BUTTON, self.__OnRemoveButtonCLicked)
        sizer_header.Add(self.button_remove)
        sizer_header.Add(4, 0)

        sizer1.Add(0, 4)
        sizer1.Add(sizer_header, 0, wx.EXPAND)
        sizer1.Add(0, 4)
        sizer1.Add(wx.StaticLine(self, size=(0, 1), style=wx.LI_HORIZONTAL), 0, wx.EXPAND)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.transfersListView = TransfersListView(self)
        sizer3.Add(self.transfersListView, 1, wx.EXPAND)

        sizer1.Add(sizer3, 1, wx.EXPAND)

        self.SetSizerAndFit(sizer1)

        wx.GetApp().transfers.Bind(Transfers.Event.ADDED, lambda transfer: wx.CallAfter(self.__OnTransferAdded, transfer))
        wx.GetApp().transfers.Bind(Transfers.Event.REMOVED, lambda transfer: wx.CallAfter(self.__OnTransferRemoved, transfer))
        wx.GetApp().transfers.Bind(Transfers.Event.STATE_CHANGED, lambda state: wx.CallAfter(self.__OnStateChanged, state))

        self._UpdateTitle()


    def _UpdateTitle(self):
        infos = []

        transfers = wx.GetApp().transfers.transfers
        num_active = 0
        num_queued = 0
        try:
            for transfer in transfers:
                if transfer.state == Transfer.State.INIT or transfer.state == Transfer.State.FINISHED:
                    num_queued += 1
                elif transfer.state == Transfer.State.CONNECTING or transfer.state == Transfer.State.TRANSFERING:
                    num_active += 1
        except:
            pass

        if num_active > 0:
            infos.append(_("{} active").format(num_active))

        if num_queued > 0:
            infos.append(_("{} queued").format(num_queued))

        if wx.GetApp().transfers.completed > 0:
            infos.append(_("{} completed").format(wx.GetApp().transfers.completed))

        if len(infos) > 0:
            self.title.SetLabel(_('Downloads')+' ({})'.format(', '.join(infos)))
        else:
            self.title.SetLabel(_('Downloads'))


    def __OnTransferAdded(self, transfer):
        self.__UpdateStopButton()
        self._UpdateTitle()
        self.Refresh()


    def __OnTransferRemoved(self, transfer):
        self.__UpdateStopButton()
        self._UpdateTitle()
        self.Refresh()


    def __OnStateChanged(self, state):
        self.__UpdateStopButton()
        self._UpdateTitle()
        self.Refresh()


    def __UpdateStopButton(self):
        state = wx.GetApp().transfers.state
        if state == Transfers.State.IDLE:
            if len(wx.GetApp().transfers.transfers) > 0:
                self.button_stop.SetLabel(_("Start"))
                self.button_stop.Enable()
            else:
                self.button_stop.SetLabel(_("Start"))
                self.button_stop.Disable()
        elif state == Transfers.State.RUNNING:
            self.button_stop.SetLabel(_("Stop"))
            self.button_stop.Enable()


    def __OnStopButtonClicked(self, event):
        transfers = wx.GetApp().transfers
        if transfers.state == Transfers.State.IDLE:
            transfers.Start()
        elif transfers.state == Transfers.State.RUNNING:
            if transfers.transfers[0].state == Transfer.State.TRANSFERING:
                result = wx.MessageBox(_("The currently downloading file will be incomplete if you stop the download.\nPlease note that downloads can not be resumed. \nDo you want to stop the download nevertheless?"), _("Download in progress"), wx.YES_NO)
                if result == wx.YES:
                    transfers.Stop()
            else:
                transfers.Stop()
        else:
            pass


    def __OnRemoveButtonCLicked(self, event):
        listView = self.transfersListView
        if listView.GetSelectedItemCount() == 0:
            return

        item = listView.GetFirstSelected()

        transfers = wx.GetApp().transfers
        transfer = transfers.transfers[item]
        if transfer.state == Transfer.State.TRANSFERING:
            result = wx.MessageBox(_("The file is currently downloading.\nThe file will be incomplete if you remove the download.\nDo you want to remove the download nevertheless?"), _("Download in progress"), wx.YES_NO)
            if result == wx.YES:
                transfers.Remove(transfer)
            else:
                pass
        else:
            transfers.Remove(transfer)

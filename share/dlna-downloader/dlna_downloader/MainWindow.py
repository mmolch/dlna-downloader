import wx

from .transfer import Transfer
from .transfersPanel import TransfersPanel
from .content_directory_panel import ContentDirectoryPanel
from .devices_panel import DevicesPanel

import gettext
_ = gettext.gettext

class MainWindow(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, title='DLNA Downloader', style=wx.DEFAULT_FRAME_STYLE, *args, **kwargs)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        self.Bind(wx.EVT_SIZE, self.__OnSize)

        outerborder = wx.BoxSizer(wx.VERTICAL)

        self.__splitter_horizontal = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.__splitter_horizontal.SetMinimumPaneSize(150); # Prevent unsplitting
        self.__splitter_vertical = wx.SplitterWindow(self.__splitter_horizontal, style=wx.SP_LIVE_UPDATE)
        self.__splitter_vertical.SetMinimumPaneSize(150); # Prevent unsplitting

        self.__devices_panel = DevicesPanel(self.__splitter_vertical)
        directory_panel = ContentDirectoryPanel(self.__splitter_vertical)
        self.__splitter_vertical.SplitVertically(self.__devices_panel, directory_panel, 1)

        transfers_panel = TransfersPanel(self.__splitter_horizontal)
        self.__splitter_horizontal.SplitHorizontally(self.__splitter_vertical, transfers_panel, 99999)

        outerborder.Add(self.__splitter_horizontal, 1, wx.EXPAND|wx.ALL, 0)
        self.SetSizerAndFit(outerborder)


    def OnClose(self, event):
        if len(wx.GetApp().transfers.transfers) > 0:
            state = wx.GetApp().transfers.transfers[0].state
            if state == Transfer.State.CONNECTING or state == Transfer.State.TRANSFERING:
                result = wx.MessageBox(_("A file is currently downloading.\nThe file will be incomplete if you close the application.\nAre you sure you want to quit?"), _("Download in progress"), wx.YES_NO)
                if result == wx.YES:
                    wx.GetApp().transfers.Stop()
                    self.DestroyLater()
                    event.Skip()
            else:
                self.DestroyLater()
                event.Skip()

        else:                
            self.DestroyLater()
            event.Skip()


    def OnDestroy(self, event):
        event.Skip()


    def __OnSize(self, event):
        self.__splitter_horizontal.SetSashPosition(9999)
        event.Skip()

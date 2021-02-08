import wx

from .settings import Settings

import gettext
_ = gettext.gettext



class SettingsDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)

        self.SetTitle("{} - DLNA Downloader".format(_("Settings")))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        borderSizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        borderSizer.Add(sizer, 1, wx.EXPAND|wx.ALL, 6)

        download_directory_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, _("Download-Directory"))
        self.download_directory = wx.DirPickerCtrl(self)
        self.download_directory.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDownloadDirectoryChanged)
        download_directory_sizer.Add(self.download_directory, 0, wx.EXPAND|wx.ALL, 6)
        sizer.Add(download_directory_sizer, 0, wx.EXPAND)


        sizer.Add(350,12)

        self.button_close = wx.Button(self, label=_("Close"))
        self.button_close.Bind(wx.EVT_BUTTON, self. OnClose)
        sizer.Add(self.button_close, 0, wx.ALIGN_RIGHT)

        self.SetSizerAndFit(borderSizer)
        self.UpdateSettings()


    def OnClose(self, event):
        self.DestroyLater()


    def UpdateSettings(self):
        settings = wx.GetApp().settings
        self.download_directory.SetPath(settings.Get('download-directory'))


    def OnDownloadDirectoryChanged(self, event):
        settings = wx.GetApp().settings
        settings.Set('download-directory', self.download_directory.GetPath())
        

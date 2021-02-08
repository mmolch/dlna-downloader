import wx
import wx.stc

import gettext
_ = gettext.gettext



class LicenseDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, style=wx.DEFAULT_FRAME_STYLE, *args, **kwargs)

        self.SetMinSize((640, 480))
        self.SetSize((640, 480))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        borderSizer = wx.BoxSizer()

        self.styled_text = wx.stc.StyledTextCtrl(self)
        text = open(wx.GetApp().GetFilePath("GPL3.txt"), "rb").read().decode('utf-8')
        self.styled_text.SetText(text)
        self.styled_text.SetReadOnly(True)
        borderSizer.Add(self.styled_text, 1, wx.EXPAND)

        self.SetSizer(borderSizer)


    def OnClose(self, event):
        self.DestroyLater()



class AboutDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)

        self.SetTitle("{} - DLNA Downloader".format(_("About")))

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        borderSizer = wx.BoxSizer()
        horizontal_sizer = wx.BoxSizer()
        path = wx.GetApp().GetFilePath("icons", "64", "dlna-downloader.png")
        bitmap = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(path))
        horizontal_sizer.Add(bitmap)
        horizontal_sizer.Add(12, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        horizontal_sizer.Add(sizer)
        borderSizer.Add(horizontal_sizer, 1, wx.EXPAND|wx.ALL, 6) # wx.ALL: All borders

        font_normal = self.GetFont()
        font_bold = self.GetFont()
        font_bold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.SetFont(font_bold)
        title_text = wx.StaticText(self, label="DLNA Downloader")
        self.SetFont(font_normal)
        sizer.Add(title_text)

        sizer.Add(0, font_normal.GetPixelSize()[1]/3)

        version_text = wx.StaticText(self, label="Version 1.0")
        sizer.Add(version_text)

        sizer.Add(0, font_normal.GetPixelSize()[1])

        created_by_text = wx.StaticText(self, label=_("Created by Moritz Molch"))
        sizer.Add(created_by_text, 0, wx.EXPAND)

        sizer.Add(0, font_normal.GetPixelSize()[1]/3)

        created_by_text = wx.StaticText(self, label=_("© 2021 | License: GPL 3"))
        sizer.Add(created_by_text, 0, wx.EXPAND)

        sizer.Add(0, font_normal.GetPixelSize()[1])

        button_sizer = wx.BoxSizer()
        sizer.Add(button_sizer, 0, wx.EXPAND)
        self.button_view_license = wx.Button(self, label=_("View License"))
        self.button_close = wx.Button(self, label=_("Close"))
        button_sizer.Add(self.button_view_license, 0)
        button_sizer.Add(font_normal.GetPixelSize()[1]*5, 0, 1)
        button_sizer.Add(self.button_close, 0)

        self.SetSizerAndFit(borderSizer)

        self.button_view_license.Bind(wx.EVT_BUTTON, lambda event: LicenseDialog(self).ShowModal())
        self.button_close.Bind(wx.EVT_BUTTON, self.OnClose)


    def OnClose(self, event):
        self.DestroyLater()

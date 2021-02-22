import wx

from pyupnp import PyUpnp

from .content_directory import ContentDirectory
from .util import MixColors

import gettext
_ = gettext.gettext

class DeviceButton(wx.Control):
    def __init__(self, parent, device=None, *args, **kwargs):
        wx.Control.__init__(self, parent, style=wx.NO_BORDER, *args, **kwargs)

        self.__state_mouseover = False
        self.__state_pressed = False

        self.__device = device

        self.SetMinClientSize((-1,50))

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.__OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.__OnEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.__OnLeaveWindow)
        self.Bind(wx.EVT_LEFT_DOWN, self.__OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.__OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.__OnLeftDClick)


    @property
    def device(self):
        return self.__device


    def __OnEraseBackground(self, event):
        pass


    def __OnLeftDClick(self, event):
        pass


    def __OnEnterWindow(self, event):
        self.__state_mouseover = True
        self.Refresh()


    def __OnLeaveWindow(self, event):
        self.__state_mouseover = False
        self.Refresh()


    def __OnLeftDown(self, event):
        self.__state_pressed = True
        directory = wx.GetApp().directory
        directory.SetObjectId("0")
        directory.SetDevice(self.__device)
        directory.Load()


    def __OnLeftUp(self, event):
        self.__state_pressed = False
        self.Refresh()


    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)))
        dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT))
        dc.Clear()

        clientRect = self.GetClientRect()

        sublabel_color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                                   wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                                   0.6)


        if wx.GetApp().directory.device == self.__device:
            dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
            sublabel_color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT),
                                        wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT),
                                        0.75)
            dc.Clear()

        else:
            if self.__state_mouseover:
                if self.__state_pressed:
                    renderer.DrawPushButton(self, dc, clientRect, wx.CONTROL_CURRENT)
                else:
                    bg_color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                                         wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                                         0.1)
                    dc.SetBrush(wx.Brush(bg_color))
                    dc.SetPen(wx.Pen(bg_color))
                    dc.DrawRectangle(clientRect)

        icon_pos = int(clientRect.height/2 - self.__device.icon.GetHeight()/2)
        dc.DrawBitmap(self.__device.icon, icon_pos, icon_pos)

        font_normal = self.GetFont()
        font_bold = self.GetFont()
        font_bold.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_bold)
        textExt = dc.GetTextExtent(self.__device.name)
        dc.DrawText(self.__device.name, 50, int(clientRect.height/2 - textExt.height/2 - textExt.height/1.8))

        dc.SetFont(font_normal)
        dc.SetTextForeground(sublabel_color)
        dc.DrawText(self.__device.modelName, 50, int(clientRect.height/2 - textExt.height/2 + textExt.height/1.8))

        event.Skip()


class DeviceList(wx.ScrolledWindow):
    def __init__(self, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, *args, **kwargs)

        # Repaint the device buttons on resize
        self.Bind(wx.EVT_SIZE, self.__OnSize)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.SetScrollbars(0, 50, 0, 0)
        self.__sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        upnp = wx.GetApp().upnp
        upnp.Bind(PyUpnp.Event.CLIENT_DEVICE_ADDED, lambda pyupnp, device: wx.CallAfter(self.__OnClientDeviceAdded, pyupnp, device))
        upnp.Bind(PyUpnp.Event.CLIENT_DEVICE_REMOVED, lambda pyupnp, device: wx.CallAfter(self.__OnClientDeviceRemoved, pyupnp, device))
        wx.GetApp().directory.Bind(ContentDirectory.Event.DEVICE_CHANGED, lambda content_directory, device: wx.CallAfter(self.__OnDeviceChanged, content_directory, device))


    def __OnDeviceChanged(self, content_directory, device):
        self.Refresh()


    def __OnSize(self, event):
        self.Refresh()
        event.Skip()


    def __OnClientDeviceAdded(self, pyupnp, device):
        self.__Rebuild()


    def __OnClientDeviceRemoved(self, pyupnp, device):
        self.__Rebuild()


    def __Rebuild(self):
        for window in self.GetChildren():
            window.DestroyLater()

        for device in sorted(wx.GetApp().upnp.client_devices.values(), key=lambda device: device.name.lower()):
            deviceButton = DeviceButton(self, device)
            self.__sizer.Add(deviceButton, 0, wx.EXPAND)
        
        self.Layout()



class DevicesPanel(wx.Control):
    def __init__(self, *args, **kwargs):
        wx.Control.__init__(self, *args, **kwargs)


        self.SetMinClientSize((270,250))
        sizer_outer = wx.BoxSizer(wx.VERTICAL)

        # Header --------------------------------------------------------------
        header_panel = wx.Panel(self)
        header_sizer_outer = wx.BoxSizer(wx.VERTICAL)
        header_sizer_inner = wx.BoxSizer(wx.HORIZONTAL)
        header_sizer_outer.Add(0, 3)
        header_sizer_outer.Add(header_sizer_inner, 1, wx.EXPAND)
        header_sizer_outer.Add(0, 3)
        header_panel.SetSizer(header_sizer_outer)

        header_sizer_inner.Add(6, 0)

        title = wx.StaticText(header_panel, label=_("Devices"))
        header_sizer_inner.Add(title, 0, wx.CENTER)
        header_sizer_inner.Add(0, 0, 1)
 
        search_button = wx.Button(header_panel, label=_("Refresh"))
        search_button.SetToolTip(_("Search for DLNA-enabled devices in the network"))
        search_button.Bind(wx.EVT_BUTTON, self.__OnSearchButtonClicked)
        header_sizer_inner.Add(search_button, 0, wx.CENTER)
        header_sizer_inner.Add(3, 0)

        sizer_outer.Add(header_panel, 0, wx.EXPAND)
        sizer_outer.Add(wx.StaticLine(self, size=(-1, 1)), 0, wx.EXPAND)

        # DeviceList --------------------------------------------------------------
        device_list = DeviceList(self)
        sizer_outer.Add(device_list, 1, wx.EXPAND)

        self.SetSizer(sizer_outer)


    def __OnSearchButtonClicked(self, event):
        try:
            for device in wx.GetApp().upnp.client_devices.values():
                device._maxage = 10
                device._timeout = 10
        except:
            pass

        wx.GetApp().upnp.DiscoverRegisteredClientServices()

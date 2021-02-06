import wx

from .content_directory import ContentDirectory
from .dlna_client_device import DlnaClientDevice
from .MainWindow import MainWindow
from .settings import Settings
from .transfer import Transfer
from .transfers import Transfers


from pyupnp import PyUpnp
from pyupnp.services import ContentDirectory1ClientService

import logging
import os
import threading

data_dir = os.path.dirname(__file__)
data_dir =  os.path.dirname(data_dir)
locale_dir = os.path.join(data_dir, 'locale')

import sys
# Needed for gettext on Windows
if sys.platform.startswith('win'):
    import locale
    if os.getenv('LANGUAGE') is None:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANGUAGE'] = lang

import gettext
gettext.bindtextdomain('dlna-downloader', locale_dir)
gettext.textdomain('dlna-downloader')
_ = gettext.gettext

#logging.basicConfig(level=logging.DEBUG)
wx.Log.SetLogLevel(0)
#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)



class App(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)

        if wx.Port == '__WXGTK__':
            gtk_additions()


    def OnInit(self):
        self.SetAppDisplayName("DLNA Downloader")

        self.settings = Settings()
        self.__data_dir = data_dir

        self.__running = True
        self.transfers = Transfers()

        self.upnp = PyUpnp()
        self.upnp.SetClientDeviceClass(DlnaClientDevice)
        self.upnp.RegisterClientService(ContentDirectory1ClientService)

        self.directory = ContentDirectory()

        self.mainWindow = MainWindow(None)
        self.SetTopWindow(self.mainWindow)
        self.mainWindow.Show()

        self.upnp.Start()
        self.upnp.DiscoverRegisteredClientServices()
        threading.Timer(5, self.upnp.DiscoverRegisteredClientServices).start()

        return True


    @property
    def data_dir(self):
        return self.__data_dir


    def GetFilePath(self, *args):
        return os.path.join(self.data_dir, *args)


    @property
    def running(self):
        return self.__running


    def OnExit(self):
        self.__running = False
        self.directory.Cancel()
        self.upnp.Stop()
        return 0


def gtk_additions():
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk

        css = b"""
paned > separator {
    border-style: none;
    background-color: transparent;
    background-image: None;
}
"""

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    except:
        pass

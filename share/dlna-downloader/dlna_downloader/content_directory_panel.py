import wx

from enum import Enum
import functools
import locale
import os
import platform
from threading import Thread
from time import sleep

from .about_dialog import AboutDialog
from .content_directory import ContentDirectory
from .mimedb import mimedb
from .settings_dialog import SettingsDialog
from .transfer import Transfer
from .transfers import Transfers
from .util import MixColors, IconFromSymbolic, SizeToString, CleanFilename

from pyupnp import PyUpnp


import gettext
_ = gettext.gettext
n_ = gettext.ngettext

import sys


class ContentDirectoryListView(wx.ListView):

    class SortOrder(Enum):
        NO_SORT = 1
        ASCENDING = 2
        DESCENDING = 3

    def __init__(self, parent, *args, **kwargs):
        wx.ListView.__init__(self, parent, style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VIRTUAL|wx.NO_BORDER|wx.LC_SINGLE_SEL, *args, **kwargs)

        self.GetGrandParent().button_download.Disable()

        self.SetMinSize((400, 150))

        self.__columns = []
        self.__directory = wx.GetApp().directory

        self.__directory.Bind(ContentDirectory.Event.STATE_CHANGED, lambda state: wx.CallAfter(self.OnDirectoryStateChanged, state))

        self.EnableAlternateRowColours()
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_LIST_COL_CLICK, self._OnColumnHeaderClicked)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.__OnItemActivated)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__OnSelectionChanged)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.__OnSelectionChanged)
        self.Bind(wx.EVT_LIST_CACHE_HINT, self.__OnSelectionChanged)
        #self.Bind(wx.EVT_LIST_, self.__OnSelectionChanged)


        # Need a column map since we don't show all columns
        self.column_map = []

        # Sorting
        self.sort_item_map = []
        self.sort_order = []
        self.sort_column = -1

        self.__selected = []
        self.__selected_items = []
        self.__CreateImageList()


    def Download(self, __event=None):
        try:
            for index in self.__selected_items:
                item = self.__directory.items[index]
                title = item[ContentDirectory.Field.TITLE]
                res = item[ContentDirectory.Field.RES]
                if ContentDirectory.Field.SIZE in item:
                    size = item[ContentDirectory.Field.SIZE]
                else:
                    size = None

                extension = "bin"
                if ContentDirectory.Field.MIMETYPE in item:
                    mimetype = item[ContentDirectory.Field.MIMETYPE]
                    if mimetype in mimedb:
                        extension = mimedb[mimetype]

                if title.endswith(extension):
                    filename = CleanFilename(title)
                else:
                    filename = "{}.{}".format(CleanFilename(title), extension)

                filepath = os.path.join(wx.GetApp().settings.Get("download-directory"), filename)
                wx.GetApp().transfers.Add(Transfer(filepath, res, size))
        except Exception as e:
            print(str(e))

    
    def __CreateImageList(self):
        # Same order as ContentDirectory.ItemType.*
        files = ("folder",
                 "document",
                 "video",
                 "music",
                 "picture")

        color_normal = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                                0.75)

        if wx.Port == "__WXMSW__":
            color_highlight = color_normal
        else:
            color_highlight = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT),
                                        wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT),
                                        0.75)

        imageList = wx.ImageList(16, 16)
        images_normal = []
        images_highlight = []

        for file in files:
            path = wx.GetApp().GetFilePath("icons", "16", file+".xpm")
            image = wx.Image(path)
            images_normal.append(IconFromSymbolic(image, color_normal).ConvertToBitmap())
            images_highlight.append(IconFromSymbolic(image, color_highlight).ConvertToBitmap())


        for image in images_normal:
            imageList.Add(image)

        for image in images_highlight:
            imageList.Add(image)

        self.AssignImageList(imageList, wx.IMAGE_LIST_SMALL)


    def __OnItemActivated(self, event):
        index = event.GetIndex()
        index = self.sort_item_map[index]
        item = self.__directory.items[index]
        
        type = item[ContentDirectory.Field.TYPE]
        if type == ContentDirectory.ItemType.CONTAINER: 
            id = item[ContentDirectory.Field.ID]
            self.__directory.SetObjectId(id)
            self.__directory.Load()
        
        else:
            self.Download()


    def OnDirectoryStateChanged(self, state):
        self.Freeze()
        if state == ContentDirectory.State.IDLE:
            self.Rebuild()
        else:
            self.SetItemCount(0)
        self.Thaw()


    def __OnSelectionChanged(self, __event):
        num_items = self.GetSelectedItemCount()
        if num_items == 0:
            self.__selected = []
            self.__selected_items = []
            self.GetGrandParent().button_download.Disable()
            __event.Skip()
            return


        self.__selected = []
        self.__selected_items = []
        item = self.GetFirstSelected()
        while item != -1:
            real_item = self.sort_item_map[item]
            self.__selected.append(real_item)
            if self.__directory.GetField(real_item, ContentDirectory.Field.TYPE) != ContentDirectory.ItemType.CONTAINER:
                self.__selected_items.append(real_item)
            item = self.GetNextSelected(item)

        if len(self.__selected_items) > 0:
            self.GetGrandParent().button_download.Enable()
        else:
            self.GetGrandParent().button_download.Disable()

        __event.Skip()


    def _OnColumnHeaderClicked(self, event):
        self.Freeze()
        if self.sort_column == self.column_map[event.Column]:
            if self.sort_order == self.SortOrder.NO_SORT:
                self.SortItems(event.Column, self.SortOrder.ASCENDING)
            elif self.sort_order == self.SortOrder.ASCENDING:
                self.SortItems(event.Column, self.SortOrder.DESCENDING)
            else:
                self.SortItems(event.Column, self.SortOrder.NO_SORT)

        else:
            self.SortItems(event.Column, self.SortOrder.ASCENDING)

        self.Thaw()
        

    def AddColumnIfAvailable(self, id, name):
        if id in self.__directory.fields:
            self.AppendColumn(name)
            self.column_map.append(id)
            self.__columns.append(id)


    def Rebuild(self):
        self.GetGrandParent().button_download.Disable()
        self.SetItemCount(0)
        self.DeleteAllColumns()

        self.__columns = []
        self.column_map = []
        self.sort_item_map = {k:k for k in range(0, len(self.__directory.items))}
        self.sort_order = None
        self.sort_column = -1
        self.__selected = []
        self.__selected_items = []

        self.AddColumnIfAvailable(ContentDirectory.Field.TITLE, _('Title'))
        self.AddColumnIfAvailable(ContentDirectory.Field.DURATION, _('Duration'))
        self.AddColumnIfAvailable(ContentDirectory.Field.SIZE, _('Size'))
        self.AddColumnIfAvailable(ContentDirectory.Field.DATE, _('Date'))
        self.AddColumnIfAvailable(ContentDirectory.Field.CHANNEL, _('Channel'))
        

        self.SetItemCount(len(self.__directory.items))

        if len(self.__columns) == 1:
            self.SetColumnWidth(0, self.GetClientSize().width)
            return

        # Let wxWidgets decide the minimum width, then add some extra space
        self.Freeze()
        _width = []
        for x in range(0, len(self.__columns)):
            self.SetColumnWidth(x, wx.LIST_AUTOSIZE)
            _width.append(self.GetColumnWidth(x))

        self.Layout()

        for i, width in enumerate(_width):
            self.SetColumnWidth(i, width+50)

        self.Thaw()
        self.Layout()


    def MapSortedToReal(self, item):
        if order == self.SortOrder.ASCENDING:
            pass
        elif order == self.SortOrder.DESCENDING:
            pass
        else:
            return item


    def MapRealToSorted(self, item):
        if self.sort_order == self.SortOrder.ASCENDING:
            pass
        elif self.sort_order == self.SortOrder.DESCENDING:
            pass
        else:
            return item

        
    def SortItems(self, column, order=SortOrder.ASCENDING):
        column = self.column_map[column]

        self.sort_column = column
        self.sort_order = order

        if order == self.SortOrder.NO_SORT:
            self.sort_item_map = {k:k for k in range(0, len(self.__directory.items))}
        else:
            reverse = order == self.SortOrder.DESCENDING
            map = {key: value for key, value in enumerate(sorted(self.sort_item_map.keys(), key=functools.cmp_to_key(self.__sort_cmp), reverse=reverse))}
            self.sort_item_map = map

        self.Refresh()


    def __sort_cmp(self, index1, index2):
        if self.sort_column == ContentDirectory.Field.SIZE:
            return self.__directory.GetField(index1, ContentDirectory.Field.SIZE) - self.__directory.GetField(index2, ContentDirectory.Field.SIZE)
        else:
            return locale.strcoll(self.__directory.GetField(index1, self.sort_column), self.__directory.GetField(index2, self.sort_column))


    def OnResize(self, event):
        event.Skip()

        # Try to work around the horizontal scrollbar showing up in Windows when shrinking the window
        if len(self.__columns) == 1:
            self.SetColumnWidth(0, self.GetClientSize().width)
            self.Layout()
            self.SetColumnWidth(0, self.GetClientSize().width-1)
            self.Layout()


    
    def OnGetItemText(self, item, column):
        item=self.sort_item_map[item]
        column = self.column_map[column]
        try:
            if column == ContentDirectory.Field.SIZE:
                size = self.__directory.GetField(item, column)
                if size >= 0:
                    return SizeToString(size)
                else:
                    return ''
            else:
                return self.__directory.GetField(item, column)

        except:
            return ''


    def OnGetItemColumnImage(self, item, column):
        item=self.sort_item_map[item]
        column = self.column_map[column]

        if column != ContentDirectory.Field.TITLE:
            return -1

        try:
            if item in self.__selected:
                return self.__directory.items[item][ContentDirectory.Field.TYPE]+5
            else:
                return self.__directory.items[item][ContentDirectory.Field.TYPE]
        except:
            return -1



class ErrorPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                          wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                          0.5)
        self.SetForegroundColour(color)

        outersizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        font_normal = self.GetFont()
        font_large = self.GetFont()
        font_large.MakeLarger()
        font_large.MakeLarger()
        
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.SetFont(font_large)
        text = wx.StaticText(self, label=_("Failed to read directory"))
        self.sizer2.Add(text, 0)

        self.SetFont(font_normal)
        self.sizer2.Add(0, font_large.GetPixelSize().height/2)

        self.__error_text = None    

        sizer.Add(self.sizer2, 1, wx.CENTER)
        outersizer.Add(sizer, 1, wx.CENTER)
        self.SetSizer(outersizer)


    def SetError(self, message):
        if self.__error_text:
            self.__error_text.Destroy()

        if message:
            self.__error_text = wx.StaticText(self, label=message)
            self.sizer2.Add(self.__error_text)
            self.Layout()

        self.Layout()


class DirectoryEmptyPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                          wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                          0.5)
        self.SetForegroundColour(color)

        outersizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        font_normal = self.GetFont()
        font_large = self.GetFont()
        font_large.MakeLarger()
        font_large.MakeLarger()
        
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.SetFont(font_large)
        text = wx.StaticText(self, label=_("The directory is empty"))
        self.sizer2.Add(text, 0)

        self.SetFont(font_normal)
        self.sizer2.Add(0, font_large.GetPixelSize().height/2)

        sizer.Add(self.sizer2, 1, wx.CENTER)
        outersizer.Add(sizer, 1, wx.CENTER)
        self.SetSizer(outersizer)



class LoadDirectoryPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        wx.GetApp().directory.Bind(ContentDirectory.Event.GOT_MORE_ITEMS, lambda: wx.CallAfter(self.__OnGotMoreItems))

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                          wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                          0.5)
        self.SetForegroundColour(color)

        outersizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        font = self.GetFont()
        font.MakeLarger()
        font.MakeLarger()
        self.SetFont(font)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, label=_("Reading directory…"))
        sizer2.Add(text, 0, wx.CENTER)

        sizer2.Add(0, 6)

        self.gauge = wx.Gauge(self, size=(300, -1), style=wx.GA_SMOOTH)
        sizer2.Add(self.gauge)

        sizer.Add(sizer2, 1, wx.CENTER)
        outersizer.Add(sizer, 1, wx.CENTER)
        self.SetSizer(outersizer)


    def __OnGotMoreItems(self):
        dir = wx.GetApp().directory
        wx.CallAfter(self.gauge.SetValue, len(dir.items))


class WaitingForDevicePanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.running = False
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                          wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                          0.5)
        self.SetForegroundColour(color)

        outersizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        font = self.GetFont()
        font.MakeLarger()
        font.MakeLarger()
        self.SetFont(font)

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, label=_("Waiting for device…"))
        sizer2.Add(text, 0, wx.CENTER)

        sizer2.Add(0, 6)

        self.gauge = wx.Gauge(self, size=(300, -1))
        
        sizer2.Add(self.gauge)

        sizer.Add(sizer2, 1, wx.CENTER)
        outersizer.Add(sizer, 1, wx.CENTER)
        self.SetSizer(outersizer)
        

    def Start(self):
        if self.running:
            return

        wx.CallAfter(self.gauge.SetValue, 0)
        self.running = True
        Thread(group=None, target=self.__WorkerThread).start()


    def Stop(self):
        self.running = False


    def __WorkerThread(self):
        while self.running:
            if self.gauge:
                wx.CallAfter(self.gauge.Pulse)
                sleep(0.1)


class WelcomePanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
                          wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                          0.5)
        self.SetForegroundColour(color)

        outersizer = wx.BoxSizer()
        sizer = wx.BoxSizer(wx.VERTICAL)
        font_normal = self.GetFont()
        font_large = self.GetFont()
        font_large.MakeLarger()
        font_large.MakeLarger()
        
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.SetFont(font_large)
        text = wx.StaticText(self, label=_("No device selected"))
        self.SetFont(font_normal)
        sizer2.Add(text, 0)

        sizer2.Add(0, font_large.GetPixelSize().height/2)


        text2 = wx.StaticText(self, label=_("Please choose a device from the device list.\nIf your device isn't shown, click on \"Refresh\" to\nmanually ask for responses from all DLNA-enabled\ndevices whithin your network."))
        sizer2.Add(text2,1, wx.EXPAND)

        sizer.Add(sizer2, 1, wx.CENTER)
        outersizer.Add(sizer, 1, wx.CENTER)
        self.SetSizer(outersizer)



class ContentDirectoryPanel(wx.Control):
    def __init__(self, *args, **kwargs):
        wx.Control.__init__(self, *args, **kwargs)

        self.__CreateMenu()


        self.SetMinSize((600, 400))

        wx.GetApp().directory.Bind(ContentDirectory.Event.STATE_CHANGED, lambda state: wx.CallAfter(self.__OnDirectoryStateChanged, state))
        wx.GetApp().directory.Bind(ContentDirectory.Event.DEVICE_CHANGED, lambda state: wx.CallAfter(self.__OnDirectoryDeviceChanged, state))

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer_header = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_header.Add(3, 0)
        self.breadcrumbs = BreadCrumbs(self)
        self.sizer_header.Add(self.breadcrumbs, 0, wx.EXPAND)
        self.sizer_header.Add(6, 0, 1)
        self.__title = wx.StaticText(self)
        self.sizer_header.Add(self.__title, 0, wx.CENTER)
        self.sizer_header.Add(6, 0, 1)

        button_panel = wx.Panel(self)
        button_panel.sizer = wx.BoxSizer()
        button_panel.SetSizer(button_panel.sizer)
        self.sizer_header.Add(button_panel)

        self.button_download = wx.Button(button_panel, wx.ID_DELETE, label=_('Download'))
        self.button_download.Disable()
        self.button_download.Bind(wx.EVT_BUTTON, self._OnDownloadButtonClicked)
        button_panel.sizer.Add(self.button_download, 0, wx.EXPAND)
        button_panel.sizer.Add(3, 0, 0)
        self.button_reload = wx.Button(button_panel, wx.ID_DELETE, label=_('Reload'))
        self.button_reload.Disable()
        self.button_reload.Bind(wx.EVT_BUTTON, lambda event: wx.GetApp().directory.Load())
        button_panel.sizer.Add(self.button_reload, 0, wx.EXPAND)

        button_panel.sizer.Add(3, 0, 0)
        button_menu_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_menu = wx.BitmapButton(button_panel, bitmap=self.__GetMenuBitmap())
        self.button_menu.Bind(wx.EVT_BUTTON, self.__OnMenuButtonClicked)
        button_menu_sizer.Add(self.button_menu, 1, wx.CENTER)
        button_panel.sizer.Add(button_menu_sizer, 0, wx.EXPAND)

        self.sizer_header.Add(3, 0)

        sizer.Add(0, 3)
        sizer.Add(self.sizer_header, 0, wx.EXPAND)
        sizer.Add(0, 3)
        sizer.Add(wx.StaticLine(self, size=(-1, 1)), 0, wx.EXPAND)


        self.notebook = wx.Simplebook(self)
        self.welcome_panel = WelcomePanel(self.notebook)
        self.contentDirectoryListView = ContentDirectoryListView(self.notebook)
        self.wait_panel = WaitingForDevicePanel(self.notebook)
        self.loadDirectoryPanel = LoadDirectoryPanel(self.notebook)
        self.errorPanel = ErrorPanel(self.notebook)
        self.empty_directory_panel = DirectoryEmptyPanel(self.notebook)

        self.notebook.AddPage(self.welcome_panel, '')
        self.notebook.AddPage(self.contentDirectoryListView, '')
        self.notebook.AddPage(self.wait_panel, '')
        self.notebook.AddPage(self.loadDirectoryPanel, '')
        self.notebook.AddPage(self.errorPanel, '')
        self.notebook.AddPage(self.empty_directory_panel, '')

        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.button_download.Bind(wx.EVT_BUTTON, self.contentDirectoryListView.Download)
        self.Bind(wx.EVT_SIZE, self.OnResize)


    def _OnDownloadButtonClicked(self, event):
        self.contentDirectoryListView.Download()

    def OnResize(self, event):
        menu_button_width = self.button_menu.GetSize()[0]
        download_button_width = self.button_download.GetSize()[0]
        reload_button_width = self.button_reload.GetSize()[0]
        title_width = self.__title.GetSize()[0]
        max_width = self.GetClientSize()[0]-menu_button_width-download_button_width-reload_button_width-title_width-24
        self.breadcrumbs.SetMaxClientSize((max_width,-1))

        if event:
            event.Skip()
        else:
            self.Layout()
        
        self.Refresh()


    def __OnDirectoryDeviceChanged(self, device):
        if device == None:
            self.SetTitle("")
            self.button_reload.Disable()
            self.wait_panel.Stop()
            self.breadcrumbs.Hide()
            self.notebook.ChangeSelection(0)


    def __OnDirectoryStateChanged(self, state):
        directory = wx.GetApp().directory

        if directory.device:
            self.button_reload.Enable()
        else:
            self.button_reload.Disable()

        if state == ContentDirectory.State.IDLE:
            self.wait_panel.Stop()
            if directory.device == None:
                self.breadcrumbs.Hide()
                self.notebook.ChangeSelection(0)
                self.SetTitle("")
            else:
                if len(directory.items) > 0:
                    self.notebook.ChangeSelection(1)
                    try:
                        num_containers = directory.statistics[ContentDirectory.Statistic.NUM_CONTAINERS]
                        num_items = directory.statistics[ContentDirectory.Statistic.NUM_ITEMS]

                        entries = []
                        if num_containers > 0:
                            str_containers = n_("%(num)d Directory", "%(num)d Directories", num_containers) % {'num':num_containers}
                            entries.append(str_containers)
                        
                        if num_items > 0:
                            str_items = n_("%(num)d File", "%(num)d Files", num_items) % {'num':num_items}
                            entries.append(str_items)

                            size_overall = directory.statistics[ContentDirectory.Statistic.SIZE_OVERALL]
                            if size_overall > 0:
                                entries.append(SizeToString(size_overall))

                        self.SetTitle(', '.join(entries))
                    except Exception as e:
                        print(e)
                        self.SetTitle("")
                else:
                    self.notebook.ChangeSelection(5)
                    self.SetTitle("")
        elif state == ContentDirectory.State.CONNECTING:
            self.SetTitle("")
            self.wait_panel.Start()
            self.notebook.ChangeSelection(2)
        elif state == ContentDirectory.State.DOWNLOADING:
            self.SetTitle("")
            self.loadDirectoryPanel.gauge.SetRange(directory.items_total)
            self.loadDirectoryPanel.gauge.SetValue(len(directory.items))
            self.notebook.ChangeSelection(3)
            self.wait_panel.Stop()
        elif state == ContentDirectory.State.ERROR:
            self.SetTitle("")
            self.errorPanel.SetError(directory.error_message)
            self.notebook.ChangeSelection(4)
            self.wait_panel.Stop()


    def __GetMenuBitmap(self):
        self.Layout()

        max_height = self.button_download.GetSize().Height
        new_size = int(max_height/12)*12
        new_size = max_height-10
        
        try:
            path = wx.GetApp().GetFilePath("icons", "64", "menu.xpm")
            image = wx.Image()
            if not image.LoadFile(path):
                return None

            color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK),
                            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                            0.6)

            image = IconFromSymbolic(image, color)

            if wx.Port == "__WXMSW__":
                image = image.Scale(new_size, new_size, wx.IMAGE_QUALITY_BICUBIC)
            else:
                image = image.Scale(new_size, new_size)

            return image.ConvertToBitmap()
        except Exception as e:
            print(e)
            return None


    def __CreateMenu(self):
        self.menu = wx.Menu()
        item = self.menu.Append(10, _("&Settings…"))
        item = self.menu.Append(11, _("&About…"))
        self.menu.AppendSeparator()
        item = self.menu.Append(12, _("&Quit"))
        self.menu.Bind(wx.EVT_MENU, self.__OnMenuItemActivated)


    def __OnMenuButtonClicked(self, event):
        self.button_menu.PopupMenu(self.menu)
        event.Skip()


    def __OnMenuItemActivated(self, event):
        id = event.GetId()
        if id == 10: # Settings
            SettingsDialog(self).ShowModal()
        elif id == 11: # About
            AboutDialog(self).ShowModal()
        elif id == 12: # Quit
            wx.GetApp().GetTopWindow().Close()


    def SetTitle(self, title):
        if self.__title.GetLabel() == title:
            return

        self.__title.SetLabel(title)
        self.OnResize(None)


class BreadCrumbButton(wx.Panel):
    def __init__(self, parent, id='', name='', *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.__id = id
        self.__name = name

        self.__state_mouseover = False
        self.__state_pressed = False

        self.Bind(wx.EVT_ENTER_WINDOW, self.__OnEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.__OnLeaveWindow)
        self.Bind(wx.EVT_LEFT_DOWN, self.__OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.__OnLeftUp)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.__OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.SetBackgroundColour('blue')
        self.GetParent().Refresh()

        dc = wx.MemoryDC()
        text_extent = dc.GetTextExtent(self.__name)
        dc.Destroy()

        self.SetMinSize((text_extent[0]+text_extent[1], text_extent[1]))


    def __OnEnterWindow(self, event):
        self.__state_mouseover = True
        self.Refresh()


    def __OnLeaveWindow(self, event):
        self.__state_mouseover = False
        self.Refresh()


    def __OnLeftDown(self, event):
        if wx.GetApp().directory.object_id == self.__id:
            return

        self.GetGrandParent().button_download.Disable()
        directory = wx.GetApp().directory
        directory.SetObjectId(self.__id)
        wx.GetApp().directory.Load()


    def __OnLeftUp(self, event):
        self.Refresh()

    def __OnEraseBackground(self, event):
        pass


    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)))
        dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT))
        dc.Clear()

        clientRect = self.GetClientRect()

        if wx.GetApp().directory.object_id == self.__id:
            dc.SetBackground(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
            dc.Clear()

        else:
            if self.__state_mouseover:
                    bg_color = MixColors(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK),
                                         wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT),
                                         0.1)
                    dc.SetBrush(wx.Brush(bg_color))
                    dc.SetPen(wx.Pen(bg_color))
                    dc.DrawRectangle(clientRect)

        dc.DrawLabel(self.__name, self.GetClientRect(), wx.ALIGN_CENTER)

        event.Skip()


class BreadCrumbs(wx.Control):
    def __init__(self, *args, **kwargs):
        wx.Control.__init__(self, *args, **kwargs)

        self.__path = {}

        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        wx.GetApp().directory.Bind(ContentDirectory.Event.DEVICE_CHANGED, self.__OnDirChanged)
        wx.GetApp().directory.Bind(ContentDirectory.Event.OBJECT_ID_CHANGED, self.__OnDirChanged)

        self.sizer = wx.BoxSizer()
        self.SetSizer(self.sizer)

        self.Hide()

    def SetObjectId(self, object_id):
        self.DestroyChildren()
        path = wx.GetApp().directory.GetHierarchy()
        

    def SetPath(self, path):
        if self.__path == path:
            return

        self.__path = path
        self.Refresh()
        self.GetParent().Layout()

        self.DestroyChildren()

        if not path:
            self.Hide()
            self.GetParent().Layout()
            return

        for item in path:
            id, name = item
            but = BreadCrumbButton(self, id, name)
            self.sizer.Add(but, 0, wx.EXPAND)

        
        self.Show()
        self.GetParent().OnResize(None)


    def __OnDirChanged(self, _):
        self.SetPath(wx.GetApp().directory.GetHierarchy())


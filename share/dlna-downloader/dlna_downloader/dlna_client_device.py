from pyupnp import ClientDevice

import wx

from urllib.request import urlopen
from _io import BytesIO



class DlnaClientDevice(ClientDevice):
    def __init__(self, *args, **kwargs):
        ClientDevice.__init__(self, *args, **kwargs)

        self.__GetModelName()
        self.__GetIcon()


    def __GetModelName(self):
        try:
            self.__modelName = self.FindInDescription("d:device/d:modelName").text
        except:
            self.__modelName = None


    @property
    def modelName(self):
        return self.__modelName


    def __GetIcon(self):

        icon_png = None
        icon_jpg = None
        icon_fallback = None

        try:
            iconList = self.FindInDescription('d:device/d:iconList')
            for icon in iconList:
                width = int(self.FindInDescription('d:width', icon).text)
                mimetype = self.FindInDescription('d:mimetype', icon).text
                
                if width >= 32 and mimetype == 'image/png':
                    icon_png = icon
                    break
                elif width >= 32 and mimetype == 'image/jpeg':
                    icon_jpg = icon
                else:
                    if icon_fallback:
                        fallback_width = int(self.FindInDescription('d:width', icon_fallback).text)
                        if fallback_width < width:
                            icon_fallback = icon
                    else:
                        icon_fallback = icon

        except Exception as e:
            self._logger.warning("{}: {}".format(self.name, str(e)))
            self.__icon = None
            return


        if icon_png:
            icon = icon_png
        elif icon_jpg:
            icon = icon_jpg
        elif icon_fallback:
            icon = icon_fallback

        try:
            icon_url = self.FindInDescription('d:url', icon).text
            icon_url = self.path_to_url(icon_url)
            icon_data = urlopen(icon_url).read()
            sbuf = BytesIO(icon_data)

            image = wx.Image(sbuf)
            image = image.Scale(32, 32, wx.IMAGE_QUALITY_BICUBIC)
            self.__icon = image.ConvertToBitmap()

        except Exception as e:
            self._logger.warning("{}: {}".format(self.name, str(e)))
            self.__icon = wx.Bitmap.FromRGBA(32, 32, 255, 255, 255, 255)
            return


    @property
    def icon(self):
        return self.__icon

from pyupnp import Object

from configparser import ConfigParser
import os
import platform



class Settings(Object):
    class Event(Object.Event):
        """
        CHANGED # callback(key, value)
        """
        CHANGED = 1


    def __init__(self):
        Object.__init__(self)

        self.__filename = self.GetSettingsFilename()
        self.__config = ConfigParser()
        self.__settings = {}

        self.Load()



    def Load(self):
        try:
            self.__config.read(self.__filename)
            self.__settings = self.__config["Settings"]
        except:
            self._logger.info("Failed to read config file")
            self.__config.read_string("[Settings]")
            self.__settings = self.__config["Settings"]
            self.LoadDefaults()


    def Save(self):
        try:
            if not os.path.exists(os.path.dirname(self.__filename)):
                os.makedirs(os.path.dirname(self.__filename))

            with open(self.__filename, 'w') as file:
                self.__config.write(file)

        except Exception as e:
            self._logger.info("Failed to write config file: {}".format(str(e)))


    def Get(self, key):
        if key in self.__settings:
            return self.__settings[key]
        else:
            return ""


    def Set(self, key, value):
        if key in self.__settings:
            if self.__settings[key] == value:
                return

        if key == 'download-directory':
            if not os.path.exists(value):
                os.makedirs(value)

        self.__settings[key] = value
        self.Save()
        self.Emit(self.Event.CHANGED, key, value)


    def GetSettingsFilename(self):
        if platform.system() == "Windows":
            app_data = os.getenv("LOCALAPPDATA")
            if not app_data:
                app_data = os.getenv("APPDATA")

            return os.path.join(app_data, "DLNA Downloader", "settings.ini")

        elif os.getenv('SNAP_USER_COMMON'):
            snap_common_dir = os.getenv('SNAP_USER_COMMON')
            return os.path.join(snap_common_dir, ".config", "dlna-downloader", "settings.conf")

        else:
            home_dir = os.getenv("HOME")
            return os.path.join(home_dir, ".config", "dlna-downloader", "settings.conf")


    def LoadDefaults(self):
        if platform.system() == "Windows":
            home_dir = os.getenv("USERPROFILE")

        elif os.getenv('SNAP_USER_COMMON'):
            home_dir = os.getenv('SNAP_USER_COMMON')

        else:
            home_dir = os.getenv("HOME")

        self.Set('download-directory', os.path.join(home_dir, "Downloads", "DLNA Downloader"))

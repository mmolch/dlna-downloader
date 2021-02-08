CC=gcc
CC_PREFIX=/opt/dev/toolchains/mingw64/i686-w64-mingw32-
CC_FLAGS=-Os -s -municode
CC_FLAGS_CONSOLE=
CC_FLAGS_WINDOWS=-mwindows
WINDRES=windres
WINDRES_PREFIX=/opt/dev/toolchains/mingw64/i686-w64-mingw32-
WINDRES_FLAGS=-J rc -O coff

all: dlna-downloader.exe

dlna-downloader.exe: dlna-downloader.c whereami.c dlna-downloader.res
	$(CC_PREFIX)$(CC) $(CC_FLAGS) $(CC_FLAGS_WINDOWS) -o $@ $^ ../runtime/python34.dll

dlna-downloader.res: dlna-downloader.rc
	$(WINDRES_PREFIX)$(WINDRES) $(WINDRES_FLAGS) -o $@ $^

clean:
	[ ! -f "dlna-downloader.res" ] || rm "dlna-downloader.res"
	[ ! -f "dlna-downloader.exe" ] || rm "dlna-downloader.exe"

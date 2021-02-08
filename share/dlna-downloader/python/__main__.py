#!/usr/bin/env python3


def main():
    import os
    import sys

    app_dir = os.path.realpath(__file__)
    app_dir = os.path.dirname(app_dir)
    data_dir = os.path.dirname(app_dir)
    sys.path.insert(0, app_dir)

    from dlna_downloader import App
    app = App(data_dir)
    app.MainLoop()


if __name__ == "__main__":
    main()

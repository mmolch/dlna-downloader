#!/usr/bin/env python3

def main():
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', dest='debug', action='store_const',
                        const=True, default=False,
                        help='Show debugging information')


    args = parser.parse_args()

    app_dir = os.path.realpath(__file__)
    app_dir = os.path.dirname(app_dir)
    data_dir = os.path.dirname(app_dir)
    sys.path.insert(0, app_dir)

    from dlna_downloader import App
    app = App(data_dir, args)
    app.MainLoop()


if __name__ == "__main__":
    main()

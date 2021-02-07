#!/usr/bin/env python3

import os
import sys

app_dir = os.path.realpath(__file__)
app_dir = os.path.dirname(app_dir)
app_dir = os.path.dirname(app_dir)
app_dir = os.path.dirname(app_dir)
data_dir= os.path.join(app_dir, 'share', 'dlna-downloader')

sys.path.insert(0, data_dir)

from dlna_downloader import App
print(data_dir)
app = App(data_dir)
app.MainLoop()

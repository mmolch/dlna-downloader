#!/usr/bin/env python3

import os
join = os.path.join
import sys
import pathlib
import compileall
from tempfile import TemporaryDirectory
import time
import shutil
import zipfile

src_dir=os.path.realpath('../../..')
data_dir = join(src_dir, 'share', 'dlna-downloader')

def copy_file(src, dest):
    path = os.path.dirname(src)
    print('Copy {}'.format(src))
    try:
        os.makedirs(join(dest, path))
    except:
        pass

    shutil.copy(src, join(dest, src))


with TemporaryDirectory() as temp_dir:
    dist_dir = join(temp_dir, 'dist')
    # Copy data from share/app directory
    os.chdir(data_dir)
    for file in pathlib.Path().glob('*'):
        if str(file) == "python":
            continue

        if file.is_dir():
            shutil.copytree(str(file), join(dist_dir, str(file)))
        else:
            shutil.copy(str(file), dist_dir)
    

    #Copy Windows runtime
    os.chdir(join(src_dir, 'dev', 'windows', 'runtime'))
    shutil.copy('dlna-downloader.exe', dist_dir)

    for file in pathlib.Path().glob('**/*.dll'):
        copy_file(str(file), dist_dir)

    for file in pathlib.Path().glob('**/*.zip'):
        copy_file(str(file), dist_dir)

    for file in pathlib.Path().glob('**/*.pyd'):
        copy_file(str(file), dist_dir)

    for file in pathlib.Path().glob('**/*.pyc'):
        copy_file(str(file), dist_dir)


    # Compile python files from share/app/python into a zip file
    zip = zipfile.PyZipFile(join(dist_dir, 'dlna-downloader.zip'), 'w', optimize=0)
    zip.writepy(join(data_dir, 'python'))
    zip.writepy(join(data_dir, 'python', 'dlna_downloader'))
    zip.writepy(join(data_dir, 'python', 'pyupnp'))
    zip.close()


    # Copy installer files
    for file in ('dlna-downloader.ico', 'DLNA Downloader.nsi'):
        shutil.copy(join(src_dir, 'dev', 'windows', 'installer', file), dist_dir)

    os.system(os.path.join(src_dir, 'dev', 'windows', 'installer', 'nsis', 'makensis.exe')+' "'+os.path.join(dist_dir, 'DLNA Downloader.nsi')+'"')

    shutil.copy(os.path.join(dist_dir, 'DLNA Downloader Setup.exe'), src_dir)

#!/usr/bin/env python3

import os
import sys
import pathlib
import compileall
from tempfile import TemporaryDirectory
import time
import shutil
import zipfile

srcdir=os.path.realpath('../../..')

def copy_file(src, dest):
    path = os.path.dirname(src)
    print('Copy {}'.format(src))
    try:
        os.makedirs(os.path.join(dest, path))
    except:
        pass

    shutil.copy(src, os.path.join(dest, src))


with TemporaryDirectory() as tmpdir:
    shutil.copy('dlna-downloader.ico', tmpdir)
    shutil.copy('DLNA Downloader.nsi', tmpdir)

    os.makedirs(os.path.join(tmpdir, 'bin'))
    os.makedirs(os.path.join(tmpdir, 'bin_'))
    shutil.copy('__main__.py', os.path.join(tmpdir, 'bin_'))

    os.chdir('../../../share/dlna-downloader')

    for file in pathlib.Path().glob('**/*.py'):
        copy_file(str(file), os.path.join(tmpdir, 'bin_'))

    os.chdir('../..')

    for file in pathlib.Path('share').glob('**/*.xpm'):
        copy_file(str(file), tmpdir)

    for file in pathlib.Path('share').glob('**/*.png'):
        copy_file(str(file), tmpdir)

    for file in pathlib.Path('share').glob('**/*.txt'):
        copy_file(str(file), tmpdir)

    for file in pathlib.Path('share').glob('**/*.mo'):
        copy_file(str(file), tmpdir)

    os.chdir('dev/windows/runtime')
    for file in pathlib.Path().glob('*.dll'):
        copy_file(str(file), tmpdir)

    shutil.copy('dlna-downloader.exe', tmpdir)

    for file in pathlib.Path().glob('*.zip'):
        copy_file(str(file), tmpdir)
        

    for file in pathlib.Path('lib').glob('**/*.dll'):
        copy_file(str(file), tmpdir)

    for file in pathlib.Path('lib').glob('**/*.pyd'):
        copy_file(str(file), tmpdir)

    for file in pathlib.Path('lib').glob('**/*.pyc'):
        copy_file(str(file), tmpdir)


    os.chdir(os.path.join(tmpdir, 'bin_'))
    zip = zipfile.PyZipFile('../bin/dlna-downloader', 'w', optimize=2)
    zip.writepy('.')
    zip.writepy('dlna_downloader')
    zip.writepy('pyupnp')
    zip.close()
    os.chdir(os.path.join(srcdir))

    shutil.rmtree(os.path.join(tmpdir, 'bin_'))

    os.system(os.path.join(srcdir, 'dev', 'windows', 'installer', 'nsis', 'makensis.exe')+' "'+os.path.join(tmpdir, 'DLNA Downloader.nsi')+'"')

    shutil.copy(os.path.join(tmpdir, 'DLNA Downloader Setup.exe'), srcdir)

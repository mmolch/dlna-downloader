@echo off

pushd ..\dev\windows\runtime
python.exe ..\..\..\bin\dlna-downloader %*
popd

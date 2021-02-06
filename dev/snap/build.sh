#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
TmpDir=$(mktemp -d '/dev/shm/dlna-downloader-snap.XXXXXXXX')
cp "${ScriptDir}/com.moritzmolch.dlna-downloader.appdata.xml"


rm -rf "${TmpDir}"

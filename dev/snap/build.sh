#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
TmpDir=$(mktemp -d '/dev/shm/dlna-downloader-snap.XXXXXXXX')

cd "${TmpDir}"

cp "${ScriptDir}/com.moritzmolch.dlna-downloader.appdata.xml" "${TmpDir}/"
cp "${ScriptDir}/com.moritzmolch.dlna-downloader.desktop" "${TmpDir}/"
cp "${ScriptDir}/snapcraft.yaml" "${TmpDir}/"
cp "${ScriptDir}/override-prime.sh" "${TmpDir}/"

mkdir "${TmpDir}/bin" && cp "${ScriptDir}/dlna-downloader" "${TmpDir}/bin/"
cp -r "${ScriptDir}/../../share" "${TmpDir}/"

snapcraft clean --use-lxd && \
snapcraft --use-lxd && \
mv "${TmpDir}/"*.snap "${ScriptDir}/"

rm -rf "${TmpDir}"

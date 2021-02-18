#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
SourceDir=${ScriptDir%/*}
SourceDir=${SourceDir%/*}
TmpDir=$(mktemp -d '/dev/shm/dlna-downloader-debian.XXXXXXXX')
VERSION=$(cat "${SourceDir}/VERSION")
TmpSourceDir="${TmpDir}/dlna-downloader-${VERSION}"
DistDir="${SourceDir}/dist/dlna-downloader-${VERSION}"

mkdir -p "${TmpSourceDir}"
cp -r "${SourceDir}/bin" "${TmpSourceDir}/"
cp -r "${SourceDir}/dev/debian/debian" "${TmpSourceDir}/"

while IFS= read -r path; do
    dir=${path%/*}
    [ -e "${TmpSourceDir}/share/${dir}" ] || mkdir -p "${TmpSourceDir}/share/${dir}"
    cp "${SourceDir}/share/${path}" "${TmpSourceDir}/share/${path}"
done <<<$(cd "${SourceDir}/share" && find \( -name '*.py' -o -name '*.xpm' -o -name '*.png' -o -name '*.txt' -o -name '*.mo' \) -printf '%P\n')

mkdir "${TmpSourceDir}/share/applications/"
cp "${ScriptDir}/dlna-downloader.desktop" "${TmpSourceDir}/share/applications/"


[ -d "${DistDir}" ] || mkdir -p "${DistDir}"
cd "${DistDir}"

dpkg-source -b "${TmpSourceDir}"
rm -rf "${TmpDir}"
exit

mkdir -p "../../dist/dlna-downloader-${VERSION}/"
#bzr export "../gnome-encfs-manager-${VERSION}/gnome-encfs-manager-${VERSION}"
cd "../gnome-encfs-manager-${VERSION}/"
dpkg-source -b gnome-encfs-manager-${VERSION}
release_PKGBUILD
release_SPEC
gpg --armor --sign --detach-sig "gnome-encfs-manager_${VERSION}.tar.xz"
rm -r "gnome-encfs-manager-${VERSION}"



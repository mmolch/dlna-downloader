#!/bin/bash

install_package() {
    echo "Downloading ${1}"
    apt-get download "${1}"
    echo "Extracting ${1}"
    ar x "${1}"*".deb" data.tar.xz
    rm "${1}"*".deb"
    tar -xf 'data.tar.xz'
    rm 'data.tar.xz'
}

rm -rf *

mkdir 'bin' 2>/dev/null
cp -T "${SNAPCRAFT_PROJECT_DIR}/snap/local/dlna-downloader" 'bin/dlna-downloader'

while IFS= read -r path; do
    dir=${path%/*}
    echo "${path}"
    [ -e "share/${dir}" ] || mkdir -p "share/${dir}"
    cp "${SNAPCRAFT_PROJECT_DIR}/share/${path}" "share/${path}"
done <<<$(cd "${SNAPCRAFT_PROJECT_DIR}/share" && find \( -name '*.py' -o -name '*.xpm' -o -name '*.png' -o -name '*.txt' -o -name '*.mo' \) -printf '%P\n')

python3 -m compileall -b -r 10 .
find -type f -name '*.py' -exec rm {} \;

cp -r "${SNAPCRAFT_STAGE}/data-dir" . 2>/dev/null
cp -r "${SNAPCRAFT_STAGE}/snap" . 2>/dev/null

find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod 755 bin/*
chmod 755 snap/command-chain/*
chmod 755 meta/hooks/*

install_package python3-sip
install_package python3-wxgtk4.0
install_package libwxgtk3.0-gtk3-0v5
install_package libwxbase3.0-0v5
install_package libpython3.6

exit 0

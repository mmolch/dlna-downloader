#!/bin/bash

echo '##### PRIME BEGIN ###################################'

install_package_zst() {
    echo "Downloading ${1}"
    apt-get download "${1}"
    echo "Extracting ${1}"
    ar x "${1}"*".deb" data.tar.zst
    rm "${1}"*".deb"
    tar -xf 'data.tar.zst'
    rm 'data.tar.zst'
}

install_package_xz() {
    echo "Downloading ${1}"
    apt-get download "${1}"
    echo "Extracting ${1}"
    ar x "${1}"*".deb" data.tar.xz
    rm "${1}"*".deb"
    tar -xf 'data.tar.xz'
    rm 'data.tar.xz'
}

rm -rf *

(cd "${SNAPCRAFT_PROJECT_DIR}/share" && find \( -name '*.py' -o -name '*.xpm' -o -name '*.png' -o -name '*.txt' -o -name '*.mo' \) -printf '%P\n') |
while IFS= read -r path; do
    dir=${path%/*}
    echo "${path}"
    [ -e "share/${dir}" ] || mkdir -p "share/${dir}"
    cp "${SNAPCRAFT_PROJECT_DIR}/share/${path}" "share/${path}"
done

python3 -m compileall -b -r 10 .
find -type f -name '*.py' -exec rm {} \;

cp -r "${SNAPCRAFT_PROJECT_DIR}/bin" . 2>/dev/null
cp -r "${SNAPCRAFT_STAGE}/data-dir" . 2>/dev/null
cp -r "${SNAPCRAFT_STAGE}/snap" . 2>/dev/null

find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod 755 bin/*
chmod 755 snap/command-chain/*

install_package_zst python3-sip
install_package_zst python3-wxgtk4.0
install_package_zst libwxgtk3.0-gtk3-0v5
install_package_zst libwxbase3.0-0v5
install_package_zst libpython3.10
install_package_zst python3-httplib2
install_package_xz python3-pyparsing


rm -rf 'data-dir'
ls -la
echo '##### PRIME END #####################################'
exit 0

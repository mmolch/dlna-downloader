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

#echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
#echo $PWD
#env
cp -r "${SNAPCRAFT_STAGE}/bin" . 2>/dev/null
cp -r "${SNAPCRAFT_STAGE}/share" . 2>/dev/null

cp -r "${SNAPCRAFT_STAGE}/data-dir" . 2>/dev/null
cp -r "${SNAPCRAFT_STAGE}/snap" . 2>/dev/null

#cat <<eof > 'snap/command-chain/snapcraft-runner'
##!/bin/sh
#export PATH="\$SNAP/usr/sbin:\$SNAP/usr/bin:\$SNAP/sbin:\$SNAP/bin\${PATH:+:\$PATH}"
#export PATH="\$SNAP/usr/lib/python3/dist-packages\${PATH:+:\$PATH}"
#export LD_LIBRARY_PATH="\${LD_LIBRARY_PATH:+\$LD_LIBRARY_PATH:}\$SNAP/lib:\$SNAP/usr/lib:\$SNAP/lib/x86_64-linux-gnu"
#export LD_LIBRARY_PATH="\$SNAP_LIBRARY_PATH\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
#exec "\$@"
#eof
#cat 'snap/command-chain/snapcraft-runner'

find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod 755 bin/*
chmod 755 snap/command-chain/*
chmod 755 meta/hooks/*

#install_package python3-sip
#install_package python3-wxgtk4.0
#install_package libwxgtk3.0-gtk3-0v5
#install_package libwxbase3.0-0v5
install_package libpython3.6

exit 0

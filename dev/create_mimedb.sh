#!/bin/bash

outfile="mimedb.py"

echo "mimedb = {" > "${outfile}"

while IFS= read -r file; do
    mime=$(egrep -m 1 '^<mime-type xmlns="http://www.freedesktop.org/standards/shared-mime-info" type=".*">$' "${file}" | cut -d '"' -f 4)
    ext=$(egrep -m 1 '^  <glob pattern=".*"/>$' "${file}"| cut -d '"' -f 2 | cut -d '.' -f 2)
    echo "    \"${mime}\" : \"${ext}\"," >> "${outfile}"
done <<<$(find /usr/share/mime/video -mindepth 1 -type f -name '*.xml')

while IFS= read -r file; do
    mime=$(egrep -m 1 '^<mime-type xmlns="http://www.freedesktop.org/standards/shared-mime-info" type=".*">$' "${file}" | cut -d '"' -f 4)
    ext=$(egrep -m 1 '^  <glob pattern=".*"/>$' "${file}"| cut -d '"' -f 2 | cut -d '.' -f 2)
    echo "    \"${mime}\" : \"${ext}\"," >> "${outfile}"
done <<<$(find /usr/share/mime/audio -mindepth 1 -type f -name '*.xml')

while IFS= read -r file; do
    mime=$(egrep -m 1 '^<mime-type xmlns="http://www.freedesktop.org/standards/shared-mime-info" type=".*">$' "${file}" | cut -d '"' -f 4)
    ext=$(egrep -m 1 '^  <glob pattern=".*"/>$' "${file}"| cut -d '"' -f 2 | cut -d '.' -f 2)
    echo "    \"${mime}\" : \"${ext}\"," >> "${outfile}"
done <<<$(find /usr/share/mime/image -mindepth 1 -type f -name '*.xml')

echo "}" >> "${outfile}"

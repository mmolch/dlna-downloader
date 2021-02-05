#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
cd "${ScriptDir}"

DOMAIN="dlna-downloader"

pybabel compile --domain=${DOMAIN} -d .

while IFS= read file; do
    [ -z "${file}" ] && continue

    target_dir="../../share/${DOMAIN}/locale/${file%/*}"
    [ -e "${target_dir}" ] || mkdir -p "${target_dir}"

    mv "${file}" "../../share/${DOMAIN}/locale/${file}"
done <<<$(find . -mindepth 1 -type f -name '*.mo' -printf "%P")

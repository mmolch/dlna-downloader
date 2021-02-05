#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
cd "${ScriptDir}"

DOMAIN="dlna-downloader"

pybabel extract -k n_:1,2 --omit-header --sort-output --no-location -o ${DOMAIN}.pot ..

while IFS= read dir; do
    [ -z "${dir}" ] && continue

    locale=${dir%%/*}
    pybabel update --domain=${DOMAIN} -i ${DOMAIN}.pot -d . -l "${locale}"
done <<<$(find . -mindepth 1 -type f -name '*.po' -printf "%P")

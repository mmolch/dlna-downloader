#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
cd "${ScriptDir}"

DOMAIN="dlna-downloader"

pybabel init --domain=${DOMAIN} -i ${DOMAIN}.pot -d . -l "${1}"

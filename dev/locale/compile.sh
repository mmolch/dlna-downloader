#!/bin/bash

ScriptDir=$(readlink -f "${BASH_SOURCE%/*}")
cd "${ScriptDir}"

DOMAIN="dlna-downloader"

pybabel compile --domain=${DOMAIN} -d .

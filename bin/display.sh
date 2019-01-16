#!/usr/bin/env bash

BASEPATH=$(cd `dirname $0`; pwd)'/../'

if [ -e ${BASEPATH} ]; then
    export PYTHONPATH="PYTHONPATH:${BASEPATH}" && ${BASEPATH}/py32/bin/python ${BASEPATH}/exec/display_on_web.py
fi
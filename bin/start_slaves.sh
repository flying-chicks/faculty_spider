#!/bin/bash

BASEPATH=$(cd `dirname $0`; pwd)'/../'

if [ -e ${BASEPATH} ]; then
    export PYTHONPATH="PYTHONPATH:${BASEPATH}" && ${BASEPATH}/py32/bin/python ${BASEPATH}/exec/start_slaves.py
fi
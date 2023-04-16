#!/bin/bash

export LD_LIBRARY_PATH=/opt/lampp/lib/mysql:$LD_LIBRARY_PATH
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libexpat.so

exec venv/bin/python "$@"

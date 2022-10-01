#!/bin/bash

srclang=$1
trg=$2

mode="${srclang}-${trg}"

./apudconv.py -a "${srclang}.udx" | \
    perl -wpne 's/\n/\n\0/g;' | \
    apertium -z -d . -f none "$mode" | \
    perl -wpne 's/\0//g;'

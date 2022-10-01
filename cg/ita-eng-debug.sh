#!/bin/bash

mode=$1
sent=$2

./select.py train tree -n "$sent" UD_Italian-PUD/it_pud-ud-test.conllu | ./text.sh ita "eng-${mode}"

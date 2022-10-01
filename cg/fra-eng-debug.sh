#!/bin/bash

mode=$1
sent=$2

./select.py train tree -n "$sent" UD_French-PUD/fr_pud-ud-test.conllu | ./text.sh fra "eng-${mode}"

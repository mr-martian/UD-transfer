#!/bin/bash

mode=$1
sent=$2

./select.py train tree -n "$sent" UD_Spanish-PUD/es_pud-ud-test.conllu | ./text.sh spa "eng-${mode}"

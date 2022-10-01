#!/usr/bin/env python3

import re
import sys

def blocks():
    cur = ''
    while True:
        b = sys.stdin.read(100)
        if not b:
            if cur:
                yield cur
            break
        cur += b
        if '\0' in cur:
            ls = cur.split('\0')
            yield from ls[:-1]
            cur = ls[-1]

dep_tag = re.compile(r'<(#\d+→\d+|@[\w:]+)>')
add_space = re.compile(r'\$\s*\^')
rem_space = re.compile(r'\s+(\^@?[,\.?])')
for block in blocks():
    if not block.strip():
        continue
    b2 = dep_tag.subn('', block)[0]
    b3 = add_space.subn('$ ^', b2)[0]
    b4 = rem_space.subn(r'\1', b3)[0]
    sys.stdout.write(b4+'\0')
    sys.stdout.flush()

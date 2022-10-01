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

ambig_wds = re.compile(r'(\^(?:[^/\$]|\\.)*/(?:[^/\$]|\\.)*)/(?:[^\$]|\\.)*\$')
sl_tag = re.compile('<(?=([^\$]|\\.)*/)')
for block in blocks():
    b2 = ambig_wds.subn(r'\1$', block)[0]
    b3 = sl_tag.subn('<sl:', b2)[0]
    sys.stdout.write(b3+'\0')
    sys.stdout.flush()

#!/usr/bin/env python3

import re

def tokenize(s, brackets='', comments=False):
    ret = []
    cur = ''
    esc = False
    comm = False
    for c in s:
        if esc:
            cur += c
            continue
        elif comm:
            if c == '\n':
                comm = False
        elif c == '\\':
            cur += c
            esc = True
        elif not cur:
            if not c.isspace():
                cur += c
        elif cur[0] == '"':
            cur += c
            if c == '"':
                ret.append(cur)
                cur = ''
        elif comments and c == '#':
            if cur:
                ret.append(cur)
                cur = ''
            comm = True
        elif c.isspace():
            ret.append(cur)
            cur = ''
        elif c in brackets:
            ret.append(cur)
            ret.append(c)
            cur = ''
        else:
            cur += c
    if cur:
        ret.append(cur)
    return ret

class Word:
    def __init__(self):
        self.form = ''
        self.lemma = ''
        self.upos = ''
        self.tags = []
        self.attrs = {}
        self.head = -1
        self.rel = ''
        self.wid = -1
        self.sent = None
    def children(self):
        for i, w in enumerate(self.sent.children, 1):
            if i == self.wid:
                continue
            if w.head == self.wid:
                yield w
    def from_cg(lns):
        ret = Word()
        ret.form = lns[0].strip()[2:-2]
        tgs = tokenize(lns[1].strip(), '')
        ret.lemma = tgs[0][1:-1]
        ret.upos = tgs[1]
        for t in tgs[2:]:
            if t[0] == '@':
                ret.rel = t[1:]
            elif t[0] == '#':
                n = t[1:].split('->')
                ret.wid = int(n[0])
                ret.head = int(n[1])
            elif '=' in t:
                p = t.split('=')
                ret.attrs[p[0]] = p[1]
            elif ':' in t:
                pass # vislcg3 --trace
            else:
                ret.tags.append(t)

class Sentence:
    def __init__(self, wds):
        self.children = wds
        for i, w in enumerate(self.children, 1):
            w.sent = self
    def from_cg(lns):
        wds = []
        cur = []
        for ln in lns + ['']:
            if cur and not ln.startswith('\t'):
                wds.append(Word.from_cg(cur))
                cur = []
            if ln.startswith(';') or not ln:
                continue
            cur.append(ln)
        ret = Sentence()
        ret.children = wds

class Selector:
    def __init__(self):
        self.form = None
        self.lemma = None
        self.upos = None
        self.tags = None
        self.attrs = None
        self.rel = None
        self.children = None
        self.trans_id = -1
    def match_sent(self, s):
        for w in s.children:
            m, d = self.match(w)
            if m:
                return True, d
        return False, {}
    def match_children(self, w, skip_=None):
        skip = skip_ or []
        if len(skip) == len(self.children):
            return True, {}
        for cs in self.children[len(skip):]:
            for cw in w.children():
                if cw.wid in skip:
                    continue
                m1, d1 = cs.match(cw)
                if m1:
                    m2, d2 = self.match_children(w, skip + [cw.wid])
                    if m2:
                        d2.update(d1)
                        return True, d2
        return False, {}
    def match(self, w):
        if self.form is not None and self.form != w.form:
            return False, {}
        if self.lemma is not None and self.lemma != w.lemma:
            return False, {}
        if self.upos is not None and self.upos != w.upos:
            return False, {}
        if self.rel is not None and self.rel != w.rel:
            return False, {}
        if self.tags:
            for tg in self.tags:
                if tg not in w.tags:
                    return False, {}
        if self.attrs:
            for at in self.attrs:
                if w.attrs.get(at) != self.attrs[w]:
                    return False, {}
        if self.children:
            m, d = self.match_children(w, [])
            if not m:
                return False, {}
            if self.trans_id > 0:
                d[self.trans_id] = w.wid
                return True, d
        if self.trans_id > 0:
            return True, {self.trans_id: w.wid}
        return True, {}
    def read(toks):
        if not toks or toks[0] != '[':
            raise SyntaxError("Expected selector, got '%s'" % toks[0])
        ret = Selector()
        for i, t in enumerate(toks[1:], 1):
            if t == ']':
                return ret, toks[i+1:]
            elif t.startswith('"<'):
                ret.form = t[2:-2]
            elif t[0] == '"':
                ret.lemma = t[1:-1]
            elif t.isupper():
                ret.upos = t
            elif '=' in t:
                l = t.split('=')
                ret.attrs[l[0]] = l[1]
            elif t[0] == '@':
                ret.rel = t[1:]
            elif t.isnumeric():
                ret.trans_id = int(t)
            else:
                ret.trags.append(t)
        raise SyntaxError("Unterminated selector!")

class TransferNode:
    def __init__(self):
        self.src = None
        self.form = None
        self.upos = None
        self.tags = None
        self.attrs = None
        self.head = None
        self.rel = None
    def build(self, sent, mapping):
        ws = Word()
        wo = Word()
        if self.src:
            ws = sent.children[mapping[self.src]-1]
        wo.form = self.form or ws.form
        wo.lemma = self.lemma or ws.lemma
        wo.upos = self.upos or ws.upos
        # TODO: more fine-grained
        wo.tags = self.tags[:] or ws.tags[:]
        wo.attrs = self.attrs[:] or ws.attrs[:]
        wo.head = self.head or ws.head
        wo.rel = self.rel or ws.rel

class Rule:
    def __init__(self):
        self.sel = None
        self.out = None
    def read(toks):
        pass

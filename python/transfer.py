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
        self.deleted = False
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
        return ret
    def to_cg(self):
        ls = self.tags[:]
        for a in sorted(self.attrs):
            ls.append(a + '=' + self.attrs[a])
        t = ' '.join(ls)
        d = ';' if self.deleted else ''
        return f'{d}"<{self.form}>"\n{d}\t"{self.lemma}" {self.upos} {t} @{self.rel} #{self.wid}->{self.head}'

class Sentence:
    def __init__(self, wds):
        self.children = wds
        for i, w in enumerate(self.children, 1):
            w.sent = self
    def reindex(self):
        i = 1
        for c in self.children:
            if c.deleted:
                continue
            c.wid = i
            c.sent = self
            i += 1
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
        ret = Sentence([])
        ret.children = wds
        for w in ret.children:
            w.sent = ret
        return ret
    def to_cg(self):
        return '\n'.join(w.to_cg() for w in self.children)

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
        if w.deleted:
            return False, {}
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
            else:
                d[0] = d.get(0, []) + [w.wid]
            return True, d
        if self.trans_id > 0:
            return True, {self.trans_id: w.wid}
        return True, {0: [w.wid]}
    def read_children(self, toks):
        if toks and toks[0] == '{':
            self.children = []
            t = toks[1:]
            while t and t[0] == '[':
                s, t = Selector.read(t)
                self.children.append(s)
            if t[0] != '}':
                raise SyntaxError("Unterminated child list!")
            return t[1:]
        else:
            return toks
    def read(toks):
        if not toks or toks[0] != '[':
            raise SyntaxError("Expected selector, got '%s'" % toks[0])
        ret = Selector()
        for i, t in enumerate(toks[1:], 1):
            if t == ']':
                return ret, ret.read_children(toks[i+1:])
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
        self.lemma = None
        self.upos = None
        self.tags = None
        self.attrs = None
        self.head = None
        self.rel = None
        self.children = []
    def build(self, sent, mapping):
        ws = Word()
        wo = Word()
        if self.src:
            ws = sent.children[mapping[self.src]-1]
            ws.deleted = True
        wo.form = self.form or ws.form
        wo.lemma = self.lemma or ws.lemma
        wo.upos = self.upos or ws.upos
        # TODO: more fine-grained
        wo.tags = (self.tags or ws.tags or [])[:]
        wo.attrs = self.attrs or ws.attrs
        wo.head = self.head or ws.head
        wo.rel = self.rel or ws.rel
        return wo
    def read_update(self, toks):
        if not toks[0] or toks[0] != '[':
            return toks
    def read_children(self, toks):
        if not toks[0] or toks[0] != '{':
            return toks
    def read(toks):
        if not toks:
            raise SyntaxError("Missing output node!");
        ret = TransferNode()
        t = toks
        if toks[0].isdigit():
            ret.src = int(t[0])
            t = toks[1:]
        t2 = ret.read_update(t)
        t3 = ret.read_children(t2)
        return ret, t3
    def iter_children(self):
        yield self
        for c in self.children:
            yield from c.iter_children()

class Rule:
    def __init__(self):
        self.sel = None
        self.out = None
    def read(toks):
        ret = Rule()
        ret.sel, t2 = Selector.read(toks)
        if not t2 or t2[0] != '=>':
            raise SyntaxError("Expected => between selector and action")
        ret.out, t3 = TransferNode.read(t2[1:])
        if t3[0] == ';':
            return ret, t3[1:]
        else:
            raise SyntaxError("Expected ; to terminate rule")
    def apply(self, sent):
        app, m = self.sel.match_sent(sent)
        app1 = app
        while app:
            for c in self.out.iter_children():
                sent.children.append(c.build(sent, m))
            sent.reindex()
            app, m = self.sel.match_sent(sent)
        return app1, sent

def read_corpus(stream):
    cur = []
    while True:
        l = stream.readline()
        if l.strip():
            cur.append(l)
        if cur and not l.strip():
            yield Sentence.from_cg(cur)
            cur = []
        if not l:
            break

def read_rules(stream):
    toks = tokenize(stream.read(), brackets='[]{};', comments=True)
    rules = []
    while toks:
        if toks[0] == '[':
            r, toks = Rule.read(toks)
            rules.append(r)
        else:
            raise SyntaxError("Unexpected '%s'!" % toks[0])
    return rules

def process(sent, rules):
    for i, r in enumerate(rules, 1):
        a, n = r.apply(sent)
        if a:
            print(f'Rule {i} matched!')
    return sent

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser('Modify UD trees for Apertium')
    parser.add_argument('-r', '--rules')
    parser.add_argument('-i', '--input', default='-')
    parser.add_argument('-o', '--output', default='-')
    args = parser.parse_args()

    rules = []
    with open(args.rules) as fin:
        rules = read_rules(fin)

    intxt = sys.stdin
    outtxt = sys.stdout
    if args.input != '-':
        intxt = open(args.input)
    if args.output != '-':
        outtxt = open(args.output, 'w')

    for sent in read_corpus(intxt):
        outtxt.write(process(sent, rules).to_cg() + '\n\n')

    if intxt != sys.stdin:
        intxt.close()
    if outtxt != sys.stdout:
        outtxt.close()

#!/usr/bin/env python3

import re

class LU:
    def __init__(self, idx=1, head=-1, rel='', spaceafter=True):
        self.idx = idx
        self.head = head
        self.rel = rel
        self.spaceafter = spaceafter

class ApertiumLU(LU):
    def __init__(self, lem, tags, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lem = lem
        self.tags = tags
    def match(self, other):
        if self.lem and self.lem != other.lem:
            return False
        return set(self.tags) <= set(other.tags)
    def __isub__(self, other):
        if other.lem:
            self.lem = ''
        self.tags = [t for t in self.tags if t not in other.tags]
    def __iadd__(self, other):
        if other.lem:
            self.lem = other.lem
        self.tags += other.tags
    def to_string(self):
        pieces = [self.lem] + [f'<{t}>' for t in self.tags]
        if self.rel:
            pieces.append(f'<@{self.rel}>')
        if self.head != -1:
            pieces.append(f'<#{self.idx}→{self.head}>')
        ret = '^' + ''.join(pieces) + '$'
        if self.spaceafter:
            ret += ' '
        return ret

class UDLU(LU):
    def __init__(self, lem, pos, feats, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lem = lem
        self.pos = pos
        self.feats = feats
    def match(self, other):
        if self.lem and self.lem != other.lem:
            return False
        if self.pos and self.pos != other.pos:
            return False
        return set(self.feats) <= set(other.feats)
    def __isub__(self, other):
        if other.lem:
            self.lem = ''
        if other.pos:
            self.pos = ''
        self.feats = [f for f in self.feats if f not in other.feats]
    def __iadd__(self, other):
        if other.lem:
            self.lem = other.lem
        if other.pos:
            self.pos = other.pos
        self.feats += other.feats
    def to_string(self):
        ls = ['_'] * 10
        ls[0] = str(self.idx)
        ls[2] = self.lem or '_'
        ls[3] = self.pos or '_'
        ls[5] = '|'.join(sorted(self.feats)) or '_'
        if self.head != -1:
            ls[6] = str(self.head)
        ls[7] = self.rel or '_'
        if not self.spaceafter:
            ls[9] = 'SpaceAfter=No'
        return '\t'.join(ls) + '\n'

class ConversionRule:
    def __init__(self, ap, dir, ud):
        self.ap = ap
        self.dir = dir
        self.ud = ud
    def to_ud(self, ap, ud):
        if self.dir in ['>', '<>'] and self.ap.match(ap):
            ap -= self.ap
            ud += self.ud
    def to_ap(self, ud, ap):
        if self.dir in ['<', '<>'] and self.ud.match(ud):
            ud -= self.ud
            ap += self.ap

def conll_val(ls, pos):
    if ls[pos] == '_':
        return ''
    return ls[pos]
def conll_list(ls, pos, sep):
    if ls[pos] == '_':
        return []
    return ls[pos].split(sep)
            
def parse_rules(stream):
    rules = []
    for line_ in stream:
        line = line_.strip()
        if not line or line.startswith('#'):
            continue
        ls = line.split('\t')
        if len(ls) != 6:
            # TODO: maybe error or warn here?
            continue
        ap = ApertiumLU(conll_val(ls, 0), conll_list(ls, 1, '.'))
        ud = UDLU(conll_val(ls, 3), conll_val(ls, 4), conll_list(ls, 5, '|'))
        # TODO: conll_validate <, <>, >
        rules.append(ConversionRule(ap, conll_val(ls, 2), ud))
    return rules

def ap2ud(ap, rules):
    ud = UDLU('', '', [], idx=ap.idx, head=ap.head, rel=ap.rel)
    for rl in rules:
        rl.to_ud(ap, ud)
    if ap.lem:
        ud.lem = ap.lem
    return ud

def ud2ap(ud, rules):
    ap = ApertiumLU('', [], idx=ud.idx, head=ud.head, rel=ud.rel)
    for rl in rules:
        rl.to_ap(ud, ap)
    if ud.lem:
        ap.lem = ud.lem
    return ap

ap_lem_re = re.compile(r'([^\\<$]|\\.)+')
ap_head_re = re.compile(r'<#\d+→(\d+)>')
ap_rel_re = re.compile(r'<@([^>$]+)>')
ap_tag_re = re.compile(r'<([^>]+)>')
def re_trim(line, re, group=0):
    m = re.match(line)
    if m:
        s = m.group(group)
        return line[len(s):], s
    return line, ''
def stream_ap2ud(instream, outstream, rules):
    sent_idx = 1
    for line_ in instream:
        line = line_.strip()
        if not line:
            continue
        words = []
        in_lu = False
        in_tag = False
        lem = ''
        tags = []
        while line:
            spc = False
            while line and line[0] != '^':
                if line[0] == '\\':
                    line = line[2:]
                else:
                    line = line[1:]
                spc = True
            if words:
                words[-1].spaceafter = spc
            if not line:
                break
            line = line[1:]
            lem = ''
            tags = []
            head = -1
            rel = ''
            while line and line[0] == '$':
                if line[0] == '<':
                    line, h = re_trim(line, ap_head_re, group=1)
                    if h:
                        head = int(h)
                        continue
                    line, r = re_trim(line, ap_rel_re, group=1)
                    if r:
                        rel = r
                        continue
                    line, t = re_trim(line, ap_tag_re, group=1)
                    if t:
                        tags.append(t)
                        continue
                    # something weird is going on, so just skip < for now
                    line = line[1:]
                else:
                    line, l = re_trim(line, ap_lem_re)
                    lem += l
            words.append(ApertiumLU(lem, tags,
                                    head=head, rel=rel, idx=len(words)+1))
        if not words:
            continue
        outstream.write(f'# sent_id = s{sent_idx}\n')
        sent_idx += 1
        for ap in words:
            outstream.write(ap2ud(ap, rules).to_string())
        outstream.write('\n')

def stream_ud2ap(instream, outstream, rules):
    for line_ in instream:
        line = line_.strip()
        if not line:
            outstream.write('\n')
            continue
        elif line[0] == '#':
            continue
        ls = line.split('\t')
        if len(ls) != 10:
            continue
        if '-' in ls[0] or '.' in ls[0]:
            # skip enhanced deps for now
            continue
        head = conll_val(ls, 6)
        ud = UDLU(conll_val(ls, 2), conll_val(ls, 3), conll_list(ls, 5, '|'),
                  head=(int(head) if head else -1), idx=int(ls[0]),
                  rel=conll_val(ls, 7),
                  spaceafter=('SpaceAfter=No' not in ls[9]))
        outstream.write(ud2ap(ud, rules).to_string())

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(
        'Convert between Apertium stream format and UD CoNLL-U')
    dirgp = parser.add_mutually_exclusive_group(required=True)
    dirgp.add_argument('-a', '--apertium', action='store_true',
                       help='Convert from UD to Apertium')
    dirgp.add_argument('-u', '--ud', '--conllu', action='store_true',
                       help='Convert from Apertium to UD')
    parser.add_argument('rules', action='store',
                        help='File containing conversion rules')
    args = parser.parse_args()

    with open(args.rules) as fin:
        rules = parse_rules(fin)
    if args.apertium:
        stream_ud2ap(sys.stdin, sys.stdout, rules)
    else:
        stream_ap2ud(sys.stdin, sys.stdout, rules)

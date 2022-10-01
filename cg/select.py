#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser('train/dev/test split for PUD')
parser.add_argument('split', choices=['train', 'dev', 'test'])
parser.add_argument('mode', choices=['tree', 'text'])
parser.add_argument('file', action='store')
parser.add_argument('-n', type=int)
args = parser.parse_args()

with open(args.file) as fin:
    trees = fin.read().strip().split('\n\n')
    if args.split == 'train':
        trees = trees[:800]
    elif args.split == 'dev':
        trees = trees[800:900]
    elif args.split == 'test':
        trees = trees[900:]
    if args.n:
        trees = trees[args.n-1:args.n]
    if args.mode == 'tree':
        print('\n\n'.join(trees) + '\n\n')
    elif args.mode == 'text':
        for tree in trees:
            for ln in tree.splitlines():
                if ln.startswith('# text'):
                    print(ln[9:].strip())

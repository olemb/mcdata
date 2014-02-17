#!/usr/bin/env python
"""
Print a .dat file (such as level.dat).
"""
from __future__ import print_function
import sys
from mcdata import nbt
from mcdata.nbt import Collection, Compound, List

def walk(comp):
    todo = [('', 'compound', comp)]

    while todo:
        (path, typename, value) = todo.pop()
        yield (path or '/', typename, value)

        tag = value

        if isinstance(tag, Compound):
            for name in sorted(tag, reverse=True):
                typename = tag.types[name]
                value = tag[name]
                todo.append(('{}/{}'.format(path, name),
                             typename,
                             value))
        elif isinstance(tag, List):
            typename = tag.type
            i = len(tag)
            for value in tag:
                i -= 1
                todo.append(('{}/{}'.format(path, i),
                            typename,
                            value))

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        for path, typename, value in walk(nbt.load(filename)):
            if typename in ['compound', 'list']:
                print('{}  ({})'.format(path, typename))
            else:
                print('{}  ({})  {!r}'.format(path, typename, value))

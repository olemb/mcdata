#!/usr/bin/env python
"""
Print a .dat file (such as level.dat).
"""
from __future__ import print_function
import sys
from mcdata import nbt

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        for tag, path in nbt.load(filename).walk():
            if tag.type in ['compound', 'list']:
                print(path, tag.type)
            else:
                print(path, tag.type, tag.value)

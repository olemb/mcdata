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
            print(path, tag)

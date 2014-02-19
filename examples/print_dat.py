#!/usr/bin/env python3
"""
Print a .dat file (such as level.dat).
"""
import sys
from mcdata.nbt import load, print_tree

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        print_tree(load(filename))

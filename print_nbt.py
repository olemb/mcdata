#!/usr/bin/env python
import sys
from mcdata import read_nbt_file, print_tree

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        print_tree(read_nbt_file(filename))

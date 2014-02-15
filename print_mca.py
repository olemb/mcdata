#!/usr/bin/env python
import sys
from mcdata import read_mca_file, print_tree

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        print('*****************', filename)
        chunks = read_mca_file(filename)
        for chunk in chunks:
            print_tree(chunk)

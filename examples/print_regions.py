"""
Print all regions.

Usage:

    print_regions.py [file1.mca] [...]
"""
import sys
from mcdata.nbt import print_tree
from mcdata.region import RegionFile

for filename in sys.argv[1:]:
    print('# File: {}'.format(filename))
    with RegionFile(filename) as region:
        for chunk in region:
            print_tree(chunk.data)

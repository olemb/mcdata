"""
Print tags in a file.

Todo:

* settle on a format.

* handle the empty path.
"""
from __future__ import print_function
import sys
from pprint import pprint
from mcdata import nbt

def print_tag(tag):
    for name in tag.keys():
        print(name, tag[name])

def print_some_tags(tag):
    print(tag['/'])
    print(tag['///'])
    print(tag['/Data/GameRules////keepInventory///'])
    print(tag['/Data/GameRules/keepInventory'])

def print_ints(tag):
    """Print all integer tags."""
    for t, path in tag.walk():
        if t.type == 'int':
            print(t, path)

tag = nbt.load(sys.argv[1])
print_tag(tag)
# print_some_tags(tag)
# print_ints(tag)

"""
Print tags in a file.

Todo:

* settle on a format.

* handle the empty path.
"""
from __future__ import print_function
import sys
from pprint import pprint
from mcdata.nbt import Tag, load

tree = load('level.dat')
tree['/Data/GameRules/keepInventory'].value = 2
print(tree['/Data/GameRules/keepInventory'])


tree = Tag('compound',
           {'Test': Tag('list',
                        [Tag('string', '23')])})
#print(list(tree.keys()))
print(tree['/Test/0'])

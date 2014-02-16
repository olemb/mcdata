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

data = nbt.load(sys.argv[1])
for tag, path in data.walk():
    print(path, '  ', tag)

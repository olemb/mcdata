#!/usr/bin/env python
import sys
from mcdata import nbt

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        data = nbt.load(filename)
        print(nbt.encode_json(data))

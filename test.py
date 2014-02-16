#!/usr/bin/env python
import sys
import json
from pprint import pprint
from mcdata import nbt

data = nbt.load(sys.argv[1])
print(json.dumps(data, indent=2, sort_keys=True))

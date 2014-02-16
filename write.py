import sys
import json
from pprint import pprint
from mcdata.nbt import load, save, Tag
import mcdata

def mkname(name):
    return '/home/olemb/.minecraft/saves/{}/level.dat'.format(name)

if 1:
    data = load(mkname('a'))

    data['Data']['LevelName'] = Tag('string', 'Something!')

    save(mkname('b'), data)
    data = load(mkname('b'))
    pprint(data)

import sys
import json
from pprint import pprint
from mcdata.nbt import load, save
import mcdata

def mkname(name):
    return '/home/olemb/.minecraft/saves/{}/level.dat'.format(name)

if 1:
    data = load(mkname('a'))
    save(mkname('b'), data)
    load(mkname('b'))


import sys
import json
from pprint import pprint
from mcdata.nbt import encode, decode
import mcdata

def make_filename(name):
    return '/home/olemb/.minecraft/saves/{}/level.dat'.format(name)

def load(name):
    return mcdata.nbt.load(make_filename(name))

def save(name, data):
    return mcdata.nbt.save(make_filename(name), data)

def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True))

if 0:
    if sys.argv[1:] and sys.argv[1] == 'write':
        data = load('a')
        save('b', data)
    else:
        load('b')

if 0:
    data = load('a')
    data['Data<compound>']['LevelName<string>'] = u'Something!'
    data['Data<compound>']['DayTime<long>'] = 0
    save('b', data)
    new = load('b')
    
    dump(new)

# def format_tag_name(name, typename):
#     return '{}<{}>'.format(name, typename)

class Wrapper(object):
    """
    Todo:
    
    * type checking?
    
    * check for duplicate names?
    
    * create new compound entry if name is not found
    and a type is provided. (If type is not provided, a TypeError (?)
    is raised.
    """

    def __init__(self, data):
        self.data = data

    def _find_key(self, compound, name):
        for key in compound:
            if key.rsplit('<')[0] == name:
                return key
        else:
            raise LookupError('key {} not found'.format(name))
    
    def get(self, path):
        tag = self.data
        for part in path.split('/'):
            # Find key.
            tag = tag[self._find_key(tag, part)]
        return tag

    def set(self, path, value):
        path = path.split('/')
        path, name = path[:-1], path[-1]

        tag = self.data
        for part in path:
            # Find key.
            tag = tag[self._find_key(tag, part)]

        tag[self._find_key(tag, name)] = value

    def keys(self, path=None):
        tag = self.data

        if path is not None:
            for part in path.split('/'):
                tag = tag[self._find_key(tag, part)]
                
        keys = []
        for key in tag:
            keys.append(key.split('<')[0])
        keys.sort()
        return keys

    def canonize(self, path):
        tag = self.data
        canon = []
        for part in path.split('/'):
            if '<' in part:
                name = part
            else:
                name = self._find_key(tag, part)
            canon.append(name)
            tag = tag[name]
        return '/'.join(canon)

if 1:
    data = load('a')
    wrap = Wrapper(data)
    gamerules = wrap.get('Data/GameRules')
    path = 'Data/GameRules/keepInventory'
    print(wrap.canonize(path))


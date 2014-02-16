import sys
from mcdata.region import RegionFile
from mcdata import nbt

def print_keys(data):
    print(nbt.encode_json(nbt.keys_only(data)))

for filename in sys.argv[1:]:
    f = RegionFile(filename)
    for chunk in f.iter_chunk_data():
        key = ''
        print_keys(chunk)
        entities = chunk.get('Entities<compoundlist>')
        if entities:
            print(nbt.encode_json(entities))

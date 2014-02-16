mcdata
======

Experminental library for reading and writing Minecraft data files.

This implements the NBT (Named Binary Tags) and Anvil formats.


Contact
-------

Ole Martin Bjorndalen

ombdalen@gmail.com

http://github.com/olemb/mcdata


Todo
----

* add some easily editable format.

* rename Tag (and tags) to something else?

* refer to "tag" as "tree"?

* add .mca (Anvil) support.

* support Python 3.

* support hex strings in encoder() / decoder().

* add seed generator.

* error checking: raise exception if there are bytes left over after decoding.

* type checking in the manipulator class? (Wrapper)

* rename tag to something else. (obj?)

* enter / exit for RegionFile.

* add check to Tag() for valid tag type?

* should Tag.__setitem__() create compounds if they don't exist?

* decide on a format for Tag.__repr__().

* JSON support?


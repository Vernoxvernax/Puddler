# Puddler (Emby/Jellyfin-MPV-CLI)
Emby/Jellyfin command line client, powered by mpv.

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?style=flat)](https://www.python.org/)
[![PyPI download day](https://img.shields.io/pypi/dd/puddler.svg?style=flat&logo=pypi)](https://pypi.python.org/pypi/Puddler/)
[![PyPI version shields.io](https://img.shields.io/pypi/v/puddler.svg?style=flat&logo=pypi)](https://pypi.python.org/pypi/Puddler/)
[![GitHub license](https://img.shields.io/github/license/Vernoxvernax/Puddler.svg?style=flat)](https://github.com/Vernoxvernax/Puddler/blob/main/COPYING)

[//]: # ([![Open Source? Yes!]&#40;https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?style=flat&icon=github&#41;]&#40;https://github.com/Vernoxvernax/Puddler/&#41;)
[![pypresence](https://img.shields.io/badge/using-pypresence-00bb88.svg?style=flat&logo=discord)](https://github.com/qwertyquerty/pypresence)


### Currently, in buggy alpha state?
___

### Installation:
```
$ python -m pip install Puddler --upgrade
$ python -m puddler
```

**Latest update:**
+ rewrote auth
  + script isn't going to authenticate each time, only when you've been logged out
  + device id has been set to "Puddler" (here come the duplicate device entries)
+ remove debug parameter lol

##### The auth thingy has been *written* in like 1 hour, don't expect it to run perfectly.

Also:

I will add the `setup.py` later on and figure out how to put puddler in path, so please stand by and install via pip.

___

### Information:

Currently, only the most basic features (+discord presence).

But at least both emby and jellyfin are supported.

Playback using search-term and some weird playlist mode.

___

To-Do list:

+ think of other useful features that require **0** effort to implement

---

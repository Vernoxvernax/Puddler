# Puddler (Emby/Jellyfin-MPV-CLI)
Emby/Jellyfin command line client, powered by mpv.

[![pypresence](https://img.shields.io/badge/using-pypresence-00bb88.svg?style=for-the-badge&logo=discord&logoWidth=20)](https://github.com/qwertyquerty/pypresence)

### Currently, in buggy alpha state?
___

### Installation:
```
$ python -m pip install Puddler --upgrade
$ python -m puddler
```

**Latest update:**

+ YAY, discord presence!!! Your *totally existent friends* can finally see all the fucked up shit you are binging!!!
+ a few fixes like: **not** printing duplicate episodes in series mode **¹** 
+ also moved a function to the place it belongs to and added `except: KeyboardInterrupt` to every single question after the mediaserver authentication
+ *activated* resume-playback on windows (no, I didn't just forget to copy-paste the function call)

###### ¹ This unfortunately means specials can only be found in `Specials` and won't be shown within actual seasons.
___

### Information:

Currently, only the most basic features (+discord presence).

But at least both emby and jellyfin are supported.

Playback using search-term and some weird playlist mode.

___

To-Do list:

+ up next (or whatever its called)
+ think of other useful features that require **0** effort to implement

___

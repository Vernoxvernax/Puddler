# Puddler (Emby/Jellyfin-MPV-CLI)
Emby/Jellyfin command line client, powered by mpv.

### Currently, in extreme buggy alpha state.
___

### Installation:
```
$ python -m pip install Puddler --upgrade
$ python -m puddler
```

**Latest update:**

+ kinda "full" playback support

Takes info (paused yes/no and progress) from mpv every 5 seconds and posts it to the media server. Closes session on CTRL+C. And sents progress on exiting.

You should be aware that this does however not mean, mpv will continue an item.


< will be implemented soon.

___

### Information:

Currently, not a lot of features.

But at least both emby and jellyfin are supported.

Playback using search-term and some ridiculous playlist mode.

___

Instead of a list with features, here is a to-do list:

- flawless playback of multiple episodes

___

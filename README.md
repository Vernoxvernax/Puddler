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

+ bearable support for watch-status (on/off value kind of thing)
+ the script now knows if you've watched more than 85% of a video and will then mark it as played.

###### Make sure to let it retrieve the playback_time when seeking; the function loops each second.

This does however only apply to linux users, I don't have the time to test it in a VM anymore. Will be done tomorrow.
___

### Information:

Currently, not a lot of features.

But at least both emby and jellyfin are supported.

Playback using search-term and some ridiculous playlist mode.

___

Instead of a list with features, here is a to-do list:

- flawless playback of multiple episodes
- functional playback on windows (script freezes when closing mpv without finishing it)
- actual good playback report

___
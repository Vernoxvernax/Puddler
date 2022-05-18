import time
from .playback_reporting import report_playback


def log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


def run_mpv(stream_url, item_id, head_dict):
    try:
        import mpv
        print("Using libmpv1.")
        libmpv = True
        player = mpv.MPV(ytdl=False,
                         log_handler=log,
                         loglevel='error',
                         input_default_bindings=True,
                         input_vo_keyboard=True,
                         osc=True)
    except OSError:
        print("Using mpv-jsonipc.")
        import python_mpv_jsonipc as mpv
        player = mpv.MPV(start_mpv=True,
                         log_handler=log,
                         loglevel='error')
        libmpv = False
    player.fullscreen = True
    player.play(stream_url)
    starting_playback = time.time()
    if libmpv:
        player.wait_for_playback()
        player.stop()
        player.terminate()
    else:
        player.wait_for_property("duration")
        player.wait_for_property("duration")
        player.stop()
        # player.terminate()
    ending_playback = time.time()
    report_playback(starting_playback, ending_playback, item_id, head_dict)


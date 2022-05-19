import time
import threading
from .playback_reporting import report_playback


def log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


def run_mpv(stream_url, item_list, head_dict):
    def collect_time(eof=False):
        player.wait_until_playing()
        playing = True
        while playing:
            try:
                curr = player.playback_time
            except:
                playing = False
            time.sleep(1)
        if not eof:
            report_playback(item_list, head_dict, curr)
        else:
            report_playback(item_list, head_dict, curr, True)

    # def mark_played_on_finish():
    #     player.wait_for_event('end_file')
    #     r.eof = True

    try:
        import mpv
        print("Using libmpv1.")
        libmpv = True
        player = mpv.MPV(log_handler=log,
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
    # q = threading.Thread(target=mark_played_on_finish)
    # q.start()
    # threads.append(q)
    if libmpv:
        threads = []
        r = threading.Thread(target=collect_time)
        r.start()
        threads.append(r)
        for x in threads:
            x.join()
        player.wait_for_shutdown()
        player.stop()
        player.terminate()
    else:
        player.wait_for_property("duration")
        player.wait_for_property("duration")
        player.terminate()
        player.stop()
        # player.terminate()

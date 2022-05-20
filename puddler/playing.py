import time
import threading
from .playback_reporting import report_playback


def log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


def run_mpv(stream_url, item_list, head_dict):
    def collect_time(eof=False):
        playing = True
        while playing:
            time.sleep(0.5)
            try:
                if player.playback_time is not None:
                    curr = player.playback_time
                else:
                    raise
            except:
                playing = False
        try:
            player.command("stop")
            player.terminate()
        except:
            pass
        finally:
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
                         loglevel='error',
                         ipc_socket="/tmp/mpvsocket")
        libmpv = False
    player.fullscreen = True
    player.play(stream_url)
    # q = threading.Thread(target=mark_played_on_finish)
    # q.start()
    # threads.append(q)
    r = threading.Thread(target=collect_time)
    threads = [r]
    if libmpv:
        player.wait_until_playing()
        r.start()
        player.wait_for_shutdown()
    else:
        player.wait_for_property("duration")
        r.start()
    for x in threads:
        x.join()

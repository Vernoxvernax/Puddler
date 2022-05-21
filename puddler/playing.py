import time
import threading
from .playback_reporting import *


def log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


def run_mpv(stream_url, item_list, head_dict, appname):
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

    def update_playback(playsession_id, mediasource_id):
        playing = True
        while playing:
            try:
                if player.playback_time is not None:
                    curr = int(player.playback_time * 10000000)
                    updates = {
                        "CanSeek": True,
                        "ItemId": item_list.get("Id"),
                        "PlaySessionId": playsession_id,
                        "SessionId": head_dict.get("session_info").get("Id"),
                        "MediaSourceId": mediasource_id,
                        "IsPaused": player.pause,
                        "IsMuted": player.mute,
                        "PositionTicks": curr,
                        "PlayMethod": "DirectStream",
                        "RepeatMode": "RepeatNone",
                        "EventName": "TimeUpdate"
                    }
                    update = requests.post("{}{}/Sessions/Playing/Progress".format(
                        head_dict.get("config_file").get("ipaddress"), head_dict.get("media_server")),
                        json=updates, headers=head_dict.get("request_header"))
                    time.sleep(5)
                else:
                    raise
            except:
                playing = False

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
    r = threading.Thread(target=collect_time)
    threads = [r]
    if libmpv:
        player.wait_until_playing()
        playsession_id, mediasource_id = started_playing(item_list, head_dict, appname, player.playback_time)
        s = threading.Thread(target=update_playback, args=(playsession_id, mediasource_id))
        threads.append(s)
        s.start()
        r.start()
        player.wait_for_shutdown()
    else:
        player.wait_for_property("duration")
        playsession_id, mediasource_id = started_playing(item_list, head_dict, appname, player.playback_time)
        s = threading.Thread(target=update_playback, args=(playsession_id, mediasource_id))
        threads.append(s)
        s.start()
        r.start()
    for x in threads:
        x.join()

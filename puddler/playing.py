from .playback_reporting import *
import threading


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
    player.title = "{} - Streaming: {}".format(appname, item_list.get("Name"))
    player.user_agent = "{}".format(appname)
    player.force_media_title = "{} ({})".format(item_list.get("Name"), head_dict.get("media_server_name"))
    player.play(stream_url)
    r = threading.Thread(target=collect_time)
    threads = [r]
    if libmpv:
        player.wait_until_playing()
        player.seek(item_list.get("UserData").get("PlaybackPositionTicks") / 10000000)
        playsession_id, mediasource_id = started_playing(item_list, head_dict, appname, player.playback_time)
        s = threading.Thread(target=update_playback,
                             args=(player, item_list, head_dict, playsession_id, mediasource_id))
        threads.append(s)
        s.start()
        r.start()
        player.wait_for_shutdown()
    else:
        player.wait_for_property("duration")
        player.seek(item_list.get("UserData").get("PlaybackPositionTicks") / 10000000)
        playsession_id, mediasource_id = started_playing(item_list, head_dict, appname, player.playback_time)
        s = threading.Thread(target=update_playback,
                             args=(player, item_list, head_dict, playsession_id, mediasource_id))
        threads.append(s)
        s.start()
        r.start()
    for x in threads:
        x.join()

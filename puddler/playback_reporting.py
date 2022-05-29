from .mediaserver_information import get_keypress
import pypresence
import time
import re
import requests


# Puddler discord application
global use_rpc, rpc
try:
    rpc = pypresence.Presence("980093587314343957")
    rpc.connect()
    use_rpc = True
    print("Do you want to activate Discord-Presence?\n (Y)es / (N)o\n: ", end="")
    if get_keypress("yYNn") in "Nn":
        use_rpc = False
except pypresence.exceptions.DiscordNotFound:
    use_rpc = False
    print("Discord-Presence is not available.")


def report_playback(item_list, head_dict, ending_playback=None, eof=None):
    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    session_info = head_dict.get("session_info")
    if use_rpc:
        rpc.clear()
    if eof:
        print("{}{}/Users/{}/PlayedItems/{}".format(ipaddress, media_server, user_id, item_list.get("Id")))
        mark_played = requests.post(
            "{}{}/Users/{}/PlayedItems/{}".format(ipaddress, media_server, user_id, item_list.get("Id")),
            headers=request_header)
        if mark_played.status_code == 200:
            print("Item has been marked as [PLAYED].")
    elif ending_playback is not None:
        percentage_diff = ((item_list.get("RunTimeTicks") / 10000000) - ending_playback) / (
                item_list.get("RunTimeTicks") / 10000000)
        if percentage_diff < 0.10:
            mark_played = requests.post(
                "{}{}/Users/{}/PlayedItems/{}".format(ipaddress, media_server, user_id, item_list.get("Id")),
                headers=request_header)
            if mark_played.status_code == 200:
                print("Since you've watched more than 90% of the video, it will be marked as [PLAYED].")
        elif percentage_diff < 0.90:
            progress = {
                "ItemId": item_list.get("Id"),
                "PlaySessionId": playback_info.get("PlaySessionId"),
                "SessionId": session_info.get("Id"),
                "MediaSourceId": playback_info.get("MediaSources")[0].get("Id"),
                "PositionTicks": int(ending_playback * 10000000)
            }
            requests.post(
                "{}{}/Sessions/Playing/Stopped".format(ipaddress, media_server),
                json=progress, headers=request_header)
            prog = ""
            hours = int(time.strftime("%H", time.gmtime(ending_playback)))
            minutes = int(time.strftime("%M", time.gmtime(ending_playback)))
            seconds = int(time.strftime("%S", time.gmtime(ending_playback)))
            if hours >= 1:
                prog += str(hours) + " hours, "
            if minutes >= 1:
                prog += str(minutes) + " minutes, "
            if seconds >= 1:
                prog += str(seconds) + " seconds"
            prog = re.sub(r"(,)(?!.*\1)", " and", prog)
            print("Playback progress of {} has been sent to your server.".format(prog))
        else:
            print("Item has NOT been marked as [PLAYED].")
    else:
        print("Item has NOT been marked as [PLAYED].")
    print("Waiting for all threads to finish...")


def started_playing(item_list, head_dict, appname, starttime):
    global playback_info  # this line doesnt exist
    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    session_info = head_dict.get("session_info")
    playback_info = requests.get(
        "{}{}/Items/{}/PlaybackInfo?UserId={}".format(
            ipaddress, media_server, item_list.get("Id"), user_id), headers=request_header)
    if playback_info.status_code != 200:
        print("Failed to get playback information from {}.".format(head_dict.get("media_server_name")))
        exit()
    playback_info = playback_info.json()
    playing_request = {
        "CanSeek": True,
        "ItemId": item_list.get("Id"),
        "PlaySessionId": playback_info.get("PlaySessionId"),
        "SessionId": session_info.get("Id"),
        "MediaSourceId": playback_info.get("MediaSources")[0].get("Id"),
        "IsPaused": False,
        "IsMuted": False,
        "PlaybackStartTimeTicks": item_list.get("UserData").get("PlaybackPositionTicks"),
        "PlayMethod": "DirectStream",
        "RepeatMode": "RepeatNone"
    }
    requests.post("{}{}/Sessions/Playing?format=json".format(
        ipaddress, media_server), json=playing_request,
        headers=request_header)
    return playback_info.get("PlaySessionId"), playback_info.get("MediaSources")[0].get("Id")


def update_playback(player, item_list, head_dict, playsession_id, mediasource_id):
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
                totalruntime = item_list.get("RunTimeTicks") / 10000000
                if item_list.get("Type") == "Movie" and use_rpc:
                    rpc.update(state="Streaming: {}".format(item_list.get("Name")),
                               start=int(time.time() - player.playback_time),
                               end=int(time.time() + totalruntime - player.playback_time),
                               small_image=head_dict.get("media_server_name").lower())
                elif item_list.get("Type") == "Episode" and use_rpc:
                    rpc.update(state="{} ({})".format(item_list.get("Name"), item_list.get("SeasonName")),
                               details="Streaming: {} ".format(item_list.get("SeriesName")),
                               start=int(time.time() - player.playback_time),
                               end=int(time.time() + totalruntime - player.playback_time),
                               small_image=head_dict.get("media_server_name").lower())
                requests.post("{}{}/Sessions/Playing/Progress".format(
                    head_dict.get("config_file").get("ipaddress"), head_dict.get("media_server")),
                    json=updates, headers=head_dict.get("request_header"))
                time.sleep(10)
            else:
                raise
        except:
            playing = False

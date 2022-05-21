import time
import re
import requests


def report_playback(item_list, head_dict, ending_playback=None, eof=None):
    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    session_info = head_dict.get("session_info")
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
            mark_played = requests.post(
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


def started_playing(item_list, head_dict, appname, starttime):
    global playback_info # this line doesnt exist
    starttime = int(starttime * 10000000)
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
        "PlaybackStartTimeTicks": starttime,
        "PlayMethod": "DirectStream",
        "RepeatMode": "RepeatNone"
    }
    mark_playing = requests.post(
        "{}{}/Sessions/Playing?format=json".format(
            ipaddress, media_server), json=playing_request,
        headers=request_header)
    return playback_info.get("PlaySessionId"), playback_info.get("MediaSources")[0].get("Id")

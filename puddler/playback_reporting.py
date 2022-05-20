import requests


def report_playback(item_list, head_dict, ending_playback=None, eof=None):
    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
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
        if percentage_diff < 0.15:
            mark_played = requests.post(
                "{}{}/Users/{}/PlayedItems/{}".format(ipaddress, media_server, user_id, item_list.get("Id")),
                headers=request_header)
            if mark_played.status_code == 200:
                print("Since you've watched more than 85% of the video, it will be marked as [PLAYED].")
        else:
            print("Item has NOT been marked as [PLAYED].")
    else:
        print("Item has NOT been marked as [PLAYED].")

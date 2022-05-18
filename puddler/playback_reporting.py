import requests


def report_playback(ending_playback, starting_playback, item_id, head_dict):
    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("config_file").get("user_id")
    request_header = head_dict.get("request_header")
    if ending_playback - starting_playback > 300:
        mark_played = requests.post("{}{}/Users/{}/PlayedItems/{}".format(ipaddress, media_server, user_id, item_id),
                                    headers=request_header)
        if mark_played.status_code == 200:
            print("Item has been marked as [PLAYED].")
    else:
        print("Item has NOT been marked as [PLAYED].")

import requests
import re
from .mediaserver_information import check_information

# Some mildly important variables #
global version
version = "0.2.dev2"
appname = "Puddler"
#


def green_print(text):
    print("\033[92m{}\033[00m".format(text))


def blue_print(text):
    print("\033[96m{}\033[00m".format(text))


def red_print(text):
    print("\033[91m{}\033[00m".format(text))


def choosing_media(head_dict):
    def json_alone(items):
        count = 0
        for x in items:
            count = count + 1
        if count != 1:
            return False
        else:
            return True

    def print_json(items, count):
        item_list = []
        item_list_ids = []
        item_list_type = []
        item_list_state = []
        for x in items["Items"]:
            if x["Name"] not in item_list:
                item_list.append(x["Name"])
                item_list_ids.append(x["Id"])
                item_list_type.append(x["Type"])
                if x["UserData"]["Played"] == 0:
                    item_list_state.append(0)
                    if not count:
                        print("      [{}] {} - ({})".format(item_list.index(x["Name"]), x["Name"], x["Type"]))
                    else:
                        blue_print("      [{}] {} - ({})".format("Enter", x["Name"], x["Type"]))
                        input()
                else:
                    item_list_state.append(1)
                    if not count:
                        print("      [{}] {} - ({})".format(item_list.index(x["Name"]), x["Name"], x["Type"]), end="")
                    else:
                        blue_print("      [{}] {} - ({})".format("Enter", x["Name"], x["Type"]))
                        input()
                    green_print(" [PLAYED]")
        return item_list, item_list_ids, item_list_type

    def process_input(already_asked):
        if len(item_list) > 1:
            if not already_asked:
                raw_pick = input(": ")
            else:
                raw_pick = search
            pick = int(re.sub("[^0-9]", "", raw_pick))
            if pick < (len(item_list) + 1) and not pick < 0:
                print("\nYou've chosen ", end='')
                blue_print(item_list[pick])
            else:
                print("Are you stupid?!")
                exit()
            return pick
        elif len(item_list) == 1:
            pick = 0
            return pick
        else:
            print("Nothing found.\n")
            media_name, media_id, media_type = choosing_media(head_dict)
            streaming(head_dict, media_name, media_id, media_type)

    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    items = requests.get("{}{}/Users/{}/Items/Latest"
                         .format(ipaddress, media_server, user_id), headers=request_header)
    items = {
        "Items": items.json()
    }
    item_list, item_list_ids, item_list_type = print_json(items, False)
    search = input("Please choose from above, enter a search term like \"Everything Everywhere\" or type \"ALL\" to "
                   "display literally everything.\n: ")
    if search != "ALL" and not re.search("^[0-9]+$", search):
        items = requests.get("{}{}/Items?SearchTerm={}&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, search, user_id), headers=request_header)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list, item_list_ids, item_list_type = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list, item_list_ids, item_list_type = print_json(items.json(), False)
        pick = process_input(False)
    elif search == "ALL":
        items = requests.get("{}{}/Items?SearchTerm=&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, user_id), headers=request_header)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list, item_list_ids, item_list_type = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list, item_list_ids, item_list_type = print_json(items.json(), False)
        pick = process_input(False)
    else:
        pick = process_input(True)
    return item_list[pick], item_list_ids[pick], item_list_type[pick]


def streaming(head_dict, media_name, media_id, media_type):
    from .playing import run_mpv

    def playlist(starting_pos):
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, episode_ids[starting_pos],
            request_header.get("X-{}-Token".format(media_server_name))))
        run_mpv(stream_url, episode_ids[starting_pos], head_dict)
        if not (starting_pos + 1) < len(episode_names):
            print("Ok. bye :)")
            return
        next_ep = True
        input("Welcome back. Do you want to continue playback with {}?\n[Enter]".format(
            episode_names[starting_pos + 1]))
        index = 1
        while next_ep:
            starting_pos = starting_pos + index
            print("Starting playback of {}.".format(episode_names[starting_pos]))
            stream_url = (
                "{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
                    ipaddress, media_server, episode_ids[starting_pos],
                    request_header.get("X-{}-Token".format(media_server_name))))
            run_mpv(stream_url, episode_ids[starting_pos], head_dict)
            if not (starting_pos + 1) < len(episode_names):
                next_ep = False

    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    media_server_name = head_dict.get("media_server_name")
    user_id = head_dict.get("config_file").get("user_id")
    request_header = head_dict.get("request_header")
    if media_type == "Movie":
        print("Starting mpv...".format(media_name))
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, media_id, request_header.get("X-{}-Token".format(media_server_name))))
        run_mpv(stream_url, media_id, head_dict)
    elif media_type == "Series":
        print("\n{}:".format(media_name))
        series = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
            ipaddress, media_server, user_id, media_id), headers=request_header).json()
        season_names = []
        season_ids = []
        for x in series["Items"]:
            season_names.append(x["Name"])
            season_ids.append(x["Id"])
        episode_names = []
        episode_ids = []
        episode_states = []
        for y in season_ids:
            print("   {}".format(season_names[season_ids.index(y)]))
            episodes = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
                ipaddress, media_server, user_id, y), headers=request_header).json()
            for z in episodes["Items"]:
                episode_names.append(z["Name"])
                episode_ids.append(z["Id"])
                if z["UserData"]["Played"] == 0:
                    episode_states.append(0)
                    print("      [{}] {}".format(episode_names.index(z["Name"]), z["Name"]))
                else:
                    episode_states.append(1)
                    print("      [{}] {}".format(episode_names.index(z["Name"]), z["Name"]), end="")
                    green_print(" [PLAYED]")
        starting_pos = input("Please enter which episode you want to continue at.\n: ")
        starting_pos = int(re.sub("[^0-9]", "", starting_pos))
        if starting_pos < (len(episode_ids) + 1) and not starting_pos < 0:
            print("\nYou've chosen ", end='')
            blue_print(episode_names[starting_pos])
        else:
            print("Are you stupid?!")
            exit()
        playlist(starting_pos)
    green_print("All playback has finished.\nPress [Enter] to search for something else.")
    try:
        input()
    except KeyboardInterrupt:
        exit()
    media_name, media_id, media_type = choosing_media(head_dict)
    streaming(head_dict, media_name, media_id, media_type)


def main():
    head_dict = check_information(appname, version)
    media_name, media_id, media_type = choosing_media(head_dict)
    streaming(head_dict, media_name, media_id, media_type)


main()

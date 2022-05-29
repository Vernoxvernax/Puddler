import requests
import re
from .mediaserver_information import check_information
# from .mediaserver_information import get_keypress
from .playback_reporting import *

# Some mildly important variables #
global version
version = "0.3.dev5"
appname = "Puddler"


def green_print(text):
    print("\033[92m{}\033[00m".format(text))


def blue_print(text):
    print("\033[96m{}\033[00m".format(text))


def red_print(text):
    print("\033[91m{}\033[00m".format(text))


def close_session(ipaddress, media_server, request_header):
    requests.post("{}{}/Sessions/Logout".format(
        ipaddress, media_server), headers=request_header)
    if use_rpc:
        rpc.close()
    exit()


def choosing_media(head_dict):
    def json_alone(items):
        count = 0
        for x in items:
            count = count + 1
        if count != 1:
            return False
        else:
            return True

    def print_json(items, count=False, add_to=None, tsudukeru=None):
        if not add_to:
            item_list = []
        else:
            # For smol brains
            item_list = add_to
        for x in items["Items"]:
            if x["Name"] not in item_list:
                item_list.append(x)
                if not x["UserData"]["Played"]:
                    if "PlayedPercentage" in x["UserData"]:
                        percentage = "{}%".format(int(x.get("UserData").get("PlayedPercentage")))
                        if not count:
                            print(
                                "      [{}] {} - ({}) {}".format(
                                    item_list.index(x), x.get("Name"), x.get("Type"), percentage))
                        else:
                            blue_print("      [{}] {} - ({})".format("Enter", x.get("Name"), x.get("Type")))
                            try:
                                input()
                            except KeyboardInterrupt:
                                close_session(ipaddress, media_server, request_header)
                    else:
                        if not count:
                            print(
                                "      [{}] {} - ({})".format(item_list.index(x), x.get("Name"), x.get("Type")))
                        else:
                            blue_print("      [{}] {} - ({})".format("Enter", x.get("Name"), x.get("Type")))
                            try:
                                input()
                            except KeyboardInterrupt:
                                close_session(ipaddress, media_server, request_header)
                else:
                    if not count:
                        print(
                            "      [{}] {} - ({})".format(item_list.index(x), x.get("Name"), x.get("Type")), end="")
                        green_print(" [PLAYED]")
                    else:
                        blue_print("      [{}] {} - ({}) [PLAYED]".format("Enter", x.get("Name"), x.get("Type")))
                        try:
                            input()
                        except KeyboardInterrupt:
                            close_session(ipaddress, media_server, request_header)
        return item_list

    def process_input(already_asked, item_list):
        if len(item_list) > 1:
            if not already_asked:
                try:
                    raw_pick = input(": ")
                except KeyboardInterrupt:
                    close_session(ipaddress, media_server, request_header)
            else:
                raw_pick = search
            pick = int(re.sub("[^0-9]", "", raw_pick))
            if pick < (len(item_list) + 1) and not pick < 0:
                print("\nYou've chosen ", end="")
                blue_print(item_list[pick].get("Name"))
            else:
                print("Are you stupid?!")
                exit()
            return pick
        elif len(item_list) == 1:
            pick = 0
            return pick
        else:
            print("Nothing found.\n")
            item_list = choosing_media(head_dict)
            streaming(head_dict, item_list)

    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    nextup = requests.get(
        "{}{}/Users/{}/Items/Resume"
            .format(ipaddress, media_server, user_id), headers=request_header)
    if "Id" in nextup.text:
        print("\nContinue Watching:")
        item_list = print_json(nextup.json())
        next_up = True
    else:
        next_up = False
    latest = requests.get("{}{}/Users/{}/Items/Latest"
                          .format(ipaddress, media_server, user_id), headers=request_header)
    latest = {
        "Items": latest.json()
    }
    print("\nLatest:")
    if next_up:
        item_list = print_json(latest, add_to=item_list)
    else:
        item_list = print_json(latest)
    try:
        search = input(
            "Please choose from above, enter a search term, or type \"ALL\" to "
            "display literally everything.\n: ")
    except KeyboardInterrupt:
        close_session(ipaddress, media_server, request_header)
    if search != "ALL" and not re.search("^[0-9]+$", search):
        items = requests.get("{}{}/Items?SearchTerm={}&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, search, user_id), headers=request_header)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list = print_json(items.json())
        pick = process_input(False, item_list)
    elif search == "ALL":
        items = requests.get("{}{}/Items?SearchTerm=&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, user_id), headers=request_header)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list = print_json(items.json())
        pick = process_input(False, item_list)
    else:
        pick = process_input(True, item_list)
    return item_list[pick]


def streaming(head_dict, item_list):
    from .playing import run_mpv

    def playlist(starting_pos):
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, episode_list[starting_pos].get("Id"),
            request_header.get("X-Emby-Token")))
        run_mpv(stream_url, episode_list[starting_pos], head_dict, appname)
        next_ep = True
        while next_ep:
            starting_pos = starting_pos + 1
            if starting_pos == len(episode_list):
                return
            try:
                green_print("\nWelcome back. Do you want to continue playback with:")
                blue_print("   {}".format(episode_list[starting_pos].get("Name")))
                print(" (Y)es | (N)o | (E)xit\n: ", end="")
                what = get_keypress("YyNnEe")
                if what in "Yy":
                    next_ep = True
                elif what in "Nn":
                    next_ep = False
                    return
                elif what in "Ee":
                    close_session(ipaddress, media_server, request_header)
            except KeyboardInterrupt:
                close_session(ipaddress, media_server, request_header)
            print("Starting playback of:")
            blue_print("  {}".format(episode_list[starting_pos].get("Name")))
            stream_url = (
                "{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
                    ipaddress, media_server, episode_list[starting_pos].get("Id"),
                    request_header.get("X-{}-Token".format(media_server_name))))
            run_mpv(stream_url, episode_list[starting_pos], head_dict, appname)

    ipaddress = head_dict.get("config_file").get("ipaddress")
    media_server = head_dict.get("media_server")
    media_server_name = head_dict.get("media_server_name")
    user_id = head_dict.get("user_id")
    request_header = head_dict.get("request_header")
    if item_list.get("Type") in "Movie":
        print("Starting mpv...".format(item_list.get("Name")))
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, item_list.get("Id"), request_header.get("X-{}-Token".format(media_server_name))))
        run_mpv(stream_url, item_list, head_dict, appname)
    elif item_list.get("Type") == "Series":
        print("{}:".format(item_list.get("Name")))
        series = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
            ipaddress, media_server, user_id, item_list.get("Id")), headers=request_header).json()
        season_list = []
        for x in series["Items"]:
            season_list.append(x)
        episode_list = []
        for y in season_list:
            print("   {}".format(y.get("Name")))
            episodes = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
                ipaddress, media_server, user_id, y.get("Id")), headers=request_header).json()
            for z in episodes["Items"]:
                if z in episode_list:
                    if z.get("SeasonName") != "Specials":
                        continue
                    z["fuck"] = "me"
                    episode_list.append(z)
                else:
                    episode_list.append(z)
                if z.get("UserData").get("Played") == 0:
                    print("      [{}] {}".format(episode_list.index(z), z.get("Name")))
                else:
                    print("      [{}] {}".format(episode_list.index(z), z.get("Name")), end="")
                    green_print(" [PLAYED]")
        try:
            starting_pos = input("Please enter which episode you want to continue at (number)\n: ")
        except KeyboardInterrupt:
            close_session(ipaddress, media_server, request_header)
        starting_pos = int(re.sub("[^0-9]", "", starting_pos))
        if starting_pos < (len(episode_list) + 1) and not starting_pos < 0:
            print("\nYou've chosen ", end="")
            blue_print(episode_list[starting_pos].get("Name"))
        else:
            print("Are you stupid?!")
            exit()
        playlist(starting_pos)
    elif item_list.get("Type") in "Episode Special":
        series = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
            ipaddress, media_server, user_id, item_list.get("SeriesId")), headers=request_header).json()
        season_list = []
        for x in series["Items"]:
            season_list.append(x)
        episode_list = []
        for y in season_list:
            episodes = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
                ipaddress, media_server, user_id, y.get("Id")), headers=request_header).json()
            for z in episodes["Items"]:
                if z in episode_list:
                    if z.get("SeasonName") != "Specials":
                        continue
                    z["fuck"] = "me"
                    episode_list.append(z)
                else:
                    episode_list.append(z)
        starting_pos = episode_list.index(item_list)
        playlist(starting_pos)
    else:
        print("The object type you've chosen is invalid.\nPlease report this on github.")
    green_print("All playback has finished.\nPress [Enter] to search for something else.")
    try:
        input()
    except KeyboardInterrupt:
        close_session(ipaddress, media_server, request_header)
    item_list = choosing_media(head_dict)
    streaming(head_dict, item_list)


def main():
    head_dict = check_information(appname, version)
    item_list = choosing_media(head_dict)
    streaming(head_dict, item_list)


main()

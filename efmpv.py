import requests
import socket
import json
import re
import mpv
import os.path

# Some middly important variables #
global version
version = "0.1"


#


def green_print(text):
    print("\033[92m{}\033[00m".format(text))


def blue_print(text):
    print("\033[96m{}\033[00m".format(text))


def red_print(text):
    print("\033[91m{}\033[00m".format(text))


def emby_or_jellyfin():
    global ipaddress, media_server, media_server_name
    media_server = input("What kind of server do you want to stream from?\n [1] Emby\n [2] Jellyfin\n: ")
    if media_server == "1":
        media_server = "/emby"
        media_server_name = "Emby"
        auth_header = {"Authorization": 'Emby UserId="", Client="Emby Theater", Device="efMPV", DeviceId="lol", '
                                        'Version="0.1", Token="L"'.format(version)}
    elif media_server == "2":
        media_server = ""
        media_server_name = "Jellyfin"
        auth_header = {
            "X-Emby-Authorization": 'Emby UserId="", Client="Emby Theater", Device="efMPV", DeviceId="lol", '
                                    'Version="0.1", Token="L"'.format(version),
            "Content-Type": "application/json"}
    else:
        print("Input incorrect.")
        exit()
    if os.path.isfile("emby.config.json" or "jellyfin.config.json"):
        print("\nConfiguration files found!")
        with open("{}.config.json".format(media_server_name.lower()), "r") as config:
            data = json.load(config)
            try:
                username = data["username"]
                password = data["password"]
                ipaddress = data["server"]
            except:
                print("Reading the config file failed.\nPlease remove it and restart the script.")
        use_config_input = False
        use_config = input("Do you want to use {} at the following address: {}\n (Y)es / (N)o\n: "
                           .format(media_server_name, ipaddress))
        while not use_config_input:
            if use_config == "Y" or use_config == "y":
                use_config_input = True
            elif use_config == "N" or use_config == "n":
                use_config_input = True
            else:
                print(use_config)
                use_config = input("Incorrect input. Please try again.\n: ")
    else:
        use_config = "N"
    if use_config == "N":
        print("\nSearching for local Media-Servers...\n")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
        sock.settimeout(2.0)
        broadcast_address = ('255.255.255.255', 7359)
        sock.sendto('who is EmbyServer?'.encode("utf-8"), broadcast_address)
        sock.settimeout(2.0)
        try:
            data = sock.recv(4096)
            data = json.loads(data.decode('utf-8'))
            ipaddress = data['Address']
        except socket.timeout:
            ipaddress = input(
                'Couldn\'t find any Media-Server.\nIf your server is dockerized make sure to make it uses the host '
                'network.\n'
                'Or just specify the IP-Address manually (don\'t forget the ports)\n: ')
            if not "http" in ipaddress:
                ipaddress = "http://{}".format(ipaddress)
        print("Could the Media-Server at the following address be the correct one?\n \"{}\"\n (Y)es / (N)o"
              .format(ipaddress))
        answer = input("\n: ")
        if answer in "yY":
            print("Great.")
        elif answer in "nN":
            print("Awww.")
            ipaddress = input("Go ahead smart ass (http://420.69.669.666:8096)\n: ")
            if not "http" in ipaddress:
                ipaddress = "http://{}".format(ipaddress)
        else:
            print("Ok.")
            exit()
    return auth_header


def login_auth(auth_header):
    global user_login, username
    if not os.path.isfile("{}.config.json".format(media_server_name.lower())):
        username = input("Please enter your {} username: ").format(media_server_name)
        password = input("Please enter your {} password: ").format(media_server_name)
        if " " in username or " " in password:
            print("Make sure to not include any spaces!")
            exit()
        with open("{}.config.json".format(media_server_name.lower()), "w") as output:
            stuff = {
                "username": username,
                "password": password
            }
            json.dump(stuff, output)
    else:
        with open("{}.config.json".format(media_server_name.lower()), "r") as config:
            data = json.load(config)
            try:
                username = data["username"]
                password = data["password"]
            except:
                print("\nReading the config file failed.\nPlease remove it and restart the script.")
            print("\nUsing the following {} user: {}".format(media_server_name.lower(), username))
    user_login = {
        "username": username,
        "pw": password
    }
    if media_server_name == "Jellyfin":
        user_login = json.dumps(user_login).encode("utf-8")
    authorization = requests.post("{}{}/Users/AuthenticateByName".format(ipaddress, media_server), data=user_login,
                                  headers=auth_header)
    if username.lower() in authorization.text.lower():
        green_print("Connection successfully established!\n")
        authorization = authorization.json()
        access_token = authorization["AccessToken"]
        user_id = authorization["SessionInfo"]["UserId"]
        if media_server_name == "Emby":
            basic_header = {"X-Application": "efMPV/{}".format(version),
                            "X-Emby-Token": access_token}
        else:
            basic_header = {"X-Application": "efMPV/{}".format(version),
                            "X-Emby-Token": access_token}
    else:
        red_print("Authorization failed. Please try again.")
        exit()
    return basic_header, user_id


def choosing_media(user_id, basic_header):
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
                        print("      [{}] {} - ({})".format("Enter", x["Name"], x["Type"]))
                else:
                    item_list_state.append(1)
                    if not count:
                        print("      [{}] {} - ({})".format(item_list.index(x["Name"]), x["Name"], x["Type"]), end="")
                    else:
                        print("      [{}] {} - ({})".format("Enter", x["Name"], x["Type"]), end="")
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
            print("\nYou've chosen ", end="")
            blue_print(item_list[pick])
            return pick
        else:
            print("Nothing found.\n")
            media_name, media_id, media_type = choosing_media(user_id, basic_header)
            streaming(media_name, media_id, media_type, basic_header, user_id)
    items = requests.get("{}{}/Users/{}/Items/Latest"
                         .format(ipaddress, media_server, user_id), headers=basic_header)
    items = {"Items": items.json()}
    item_list, item_list_ids, item_list_type = print_json(items, False)
    search = input("Please choose from above, enter a search term like \"Firestarter\" or type \"ALL\" to display "
                   "literally everything.\n: ")
    if search != "ALL" and not re.sub("[^0-9]", "", search):
        items = requests.get("{}{}/Items?SearchTerm={}&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, search, user_id), headers=basic_header)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list, item_list_ids, item_list_type = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list, item_list_ids, item_list_type = print_json(items.json(), False)
        pick = process_input(False)
    elif search == "ALL":
        items = requests.get("{}{}/Items?SearchTerm=&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie"
                             .format(ipaddress, media_server, user_id), headers=basic_header)
        print(items.text)
        if json_alone(items.json()["Items"]):
            print("\nOnly one item has been found.\nDo you want to select this title?")
            item_list, item_list_ids, item_list_type = print_json(items.json(), True)
        else:
            print("Please choose from the following results: ")
            item_list, item_list_ids, item_list_type = print_json(items.json(), False)
        pick = process_input(False)
    elif int(re.sub("[^0-9]", "", search)):
        pick = process_input(True)
    return item_list[pick], item_list_ids[pick], item_list_type[pick]


def my_log(loglevel, component, message):
    print('[{}] {}: {}'.format(loglevel, component, message))


def run_mpv(stream_url):
    player = mpv.MPV(ytdl=False,
                     log_handler=my_log,
                     loglevel='error',
                     input_default_bindings=True,
                     input_vo_keyboard=True,
                     osc=True)
    player.fullscreen = True
    player.play(stream_url)
    player.wait_for_playback()


def streaming(media_name, media_id, media_type, basic_header, user_id):
    def playlist(starting_pos):
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, episode_ids[starting_pos],
            basic_header.get("X-{}-Token".format(media_server_name))))
        run_mpv(stream_url)
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
                    basic_header.get("X-{}-Token".format(media_server_name))))
            run_mpv(stream_url)
            if not (starting_pos + 1) < len(episode_names):
                next_ep = False

    if media_type == "Movie":
        print("Attempting to stream {}.".format(media_name))
        stream_url = ("{}{}/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_server, media_id, basic_header.get("X-{}-Token".format(media_server_name))))
        run_mpv(stream_url)
    elif media_type == "Series":
        print("\n{}:".format(media_name))
        series = requests.get("{}{}/Users/{}/Items?ParentId={}".format(
            ipaddress, media_server, user_id, media_id), headers=basic_header).json()
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
                ipaddress, media_server, user_id, y), headers=basic_header).json()
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
            print("\nYou've chosen {}".format(episode_names[starting_pos]))
        else:
            print("Are you stupid?!")
            exit()
        playlist(starting_pos)
    green_print("All playblack finished.\nIf you want to search for something new, press [Enter]\n")
    input()
    media_name, media_id, media_type = choosing_media(user_id, basic_header)
    streaming(media_name, media_id, media_type, basic_header, user_id)


def main():
    auth_header = emby_or_jellyfin()
    basic_header, user_id = login_auth(auth_header)
    media_name, media_id, media_type = choosing_media(user_id, basic_header)
    streaming(media_name, media_id, media_type, basic_header, user_id)


main()

import requests
import socket
import json
import re
import mpv
import os.path


def ask_user_login():
    global user_login, username
    if not os.path.isfile("config.json"):
        username = input("Please enter your Emby username: ")
        password = input("Please enter your Emby password: ")
        if " " in username or " " in password:
            print("Make sure to not include any spaces!")
            exit()
        with open("config.json", "w") as output:
            stuff = {
                "username": username,
                "password": password
            }
            json.dump(stuff, output)
    else:
        with open("config.json", "r") as config:
            data = json.load(config)
            try:
                username = data["username"]
                password = data["password"]
            except:
                print("Reading the config file failed.\nPlease remove it and restart the script.")
            print("Using the following Emby account: {}".format(username))
    user_login = {
        "username": username,
        "pw": password
    }


def choosing_media(user_id, basic_header):
    search = input("Please enter a search term. (or none at all)\n: ")
    items = requests.get(
        "{}/emby/Items?SearchTerm={}&UserId={}&Recursive=true&IncludeItemTypes=Series,Movie".format(
            ipaddress, search, user_id), headers=basic_header)
    item_list = []
    item_list_ids = []
    item_list_type = []
    for x in items.json()["Items"]:
        item_list.append(x["Name"])
        item_list_ids.append(x["Id"])
        item_list_type.append(x["Type"])
    if len(item_list) > 1:
        print("\n{} items have been found.\nWhich one do you want to stream?".format(len(item_list)))
        for x in item_list:
            print("  [{}] - {} - ({})".format(item_list.index(x), x, item_list_type[item_list.index(x)]))
        raw_pick = input(": ")
        pick = int(re.sub("[^0-9]", "", raw_pick))
        if pick < (len(item_list) + 1) and not pick < 0:
            print("\nYou've chosen {}".format(item_list[pick]))
        else:
            print("Are you stupid?!")
            exit()
    elif len(item_list) == 1:
        print("\nOne item has been found.\nDo you want to stream this?".format(len(item_list)))
        input("  [Enter] - {} - ({})".format(item_list[0], item_list_type[0]))
        pick = 0
        print("\nYou've chosen {}".format(item_list[pick]))
    else:
        print("Nothing found.\nPlease try again.")
        media_name, media_id, media_type = choosing_media(user_id, basic_header)
        streaming(media_name, media_id, media_type, basic_header, user_id)
    return item_list[pick], item_list_ids[pick], item_list_type[pick]


def green_print(text):
    print("\033[92m {}\033[00m".format(text), end="")


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
        stream_url = ("{}/emby/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, episode_ids[starting_pos], basic_header.get("X-Emby-Token")))
        run_mpv(stream_url)
        if not starting_pos < len(episode_names):
            print("Ok. bye :)")
            input()
        next_ep = True
        input("Welcome back. Do you want to continue playback with {}?\n[Enter]".format(
            episode_names[starting_pos + 1]))
        index = 1
        while next_ep:
            starting_pos = starting_pos + index
            print("Starting playback of {}.".format(episode_names[starting_pos]))
            stream_url = (
                "{}/emby/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
                    ipaddress, episode_ids[starting_pos], basic_header.get("X-Emby-Token")))
            run_mpv(stream_url)
            if not (starting_pos + 1) < len(episode_names):
                next_ep = False

    if media_type == "Movie":
        print("Attempting to stream {}.".format(media_name))
        stream_url = ("{}/emby/Videos/{}/stream?Container=mkv&Static=true&SubtitleMethod=External&api_key={}".format(
            ipaddress, media_id, basic_header.get("X-Emby-Token")))
        run_mpv(stream_url)
    elif media_type == "Series":
        print("\n{}:".format(media_name))
        series = requests.get("{}/emby/Users/{}/Items?ParentId={}".format(
            ipaddress, user_id, media_id), headers=basic_header).json()
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
            episodes = requests.get("{}/emby/Users/{}/Items?ParentId={}".format(
                ipaddress, user_id, y), headers=basic_header).json()
            for z in episodes["Items"]:
                episode_names.append(z["Name"])
                episode_ids.append(z["Id"])
                if z["UserData"]["Played"] == 0:
                    episode_states.append(0)
                    print("      [{}] {}".format(episode_names.index(z["Name"]), z["Name"]))
                else:
                    episode_states.append(1)
                    print("      [{}] {}".format(episode_names.index(z["Name"]), z["Name"]), end="")
                    green_print(" [PLAYED]\n")
        starting_pos = input("Please enter which episode you want to continue at.\n: ")
        starting_pos = int(re.sub("[^0-9]", "", starting_pos))
        if starting_pos < (len(episode_ids) + 1) and not starting_pos < 0:
            print("\nYou've chosen {}".format(episode_names[starting_pos]))
        else:
            print("Are you stupid?!")
            exit()
        playlist(starting_pos)
    green_print("All playblack finished.\nContinue? [Enter]")
    media_name, media_id, media_type = choosing_media(user_id, basic_header)
    streaming(media_name, media_id, media_type, basic_header, user_id)


def main():
    global ipaddress
    print("Searching for local Emby-Servers...\n")
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
            'Couldn\'t find any Emby-Server.\nIf your server is dockerized make sure to make it uses the host network.\n'
            'Or just specify the IP-Address manually (don\'t forget the ports)\n: ')
        if not "http" in ipaddress:
            ipaddress = "http://{}".format(ipaddress)
    print("Could the Emby-Server at the following address be the correct one?\n \"{}\"".format(ipaddress))
    answer = input("(Y)es / (N)o\n: ")
    if answer in "yY":
        print("Great.\n")
    elif answer in "nN":
        print("Awww.")
        ipaddress = input("Go ahead smart ass (http://420.69.669.666:8096)\n: ")
        if not "http" in ipaddress:
            ipaddress = "http://{}".format(ipaddress)
    else:
        print("Ok.")
        exit()
    ask_user_login()
    auth_header = {"Authorization": 'Emby UserId="", Client="Emby Theater", Device="eMPV", DeviceId="lol", '
                                    'Version="1", Token="L"'}
    authorization = requests.post("{}/emby/Users/AuthenticateByName".format(ipaddress), data=user_login,
                                  headers=auth_header)
    if username.lower() in authorization.text.lower():
        print("Connection successfully established!\n")
        authorization = authorization.json()
        access_token = authorization["AccessToken"]
        user_id = authorization["SessionInfo"]["UserId"]
        basic_header = {"X-Application": "eMPV/1",
                        "X-Emby-Token": access_token}
    else:
        print("Authorization failed. Please try again.")
        exit()
    media_name, media_id, media_type = choosing_media(user_id, basic_header)
    streaming(media_name, media_id, media_type, basic_header, user_id)


main()

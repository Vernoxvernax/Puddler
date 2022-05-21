# This part of puddler asks the user for their account details, emby/jellyfin address and writes the config files.
# returns (hopefully) a dictionary containing: ip_address, user_id, a request_header (with token...) and if emby or jf
import os.path
import requests
import json
import socket
from appdirs import *


def green_print(text):
    print("\033[92m{}\033[00m".format(text))


def blue_print(text):
    print("\033[96m{}\033[00m".format(text))


def red_print(text):
    print("\033[91m{}\033[00m".format(text))


def get_keypress(allowed):
    if os.name == 'nt':
        import msvcrt
        key = msvcrt.getche().decode('ASCII')
    else:
        import getch
        key = getch.getche()
    if key not in allowed:
        print("\nInput invalid. Please try again.\n: ", end="")
        get_keypress(allowed)
    print("\n\n", end="")
    return key


def read_config(appname, media_server_name):
    with open("{}/{}.config.json".format(user_cache_dir(appname),
                                         media_server_name.lower()), "r") as config:
        data = json.load(config)
        try:
            ipaddress = data["server"]
            username = data["username"]
            password = data["password"]
        except:
            print("Couldn't read the existing config file.")
            config_file = {
                "use_config": False
            }
            return config_file
        print("Do you want to use this config?\n"
              "   Host ({}): {}\n"
              "   Username: {}\n"
              " (Y)es / (N)o\n: ".format(media_server_name, ipaddress, username), end="")
        input_hm = get_keypress("ynYN")
        if input_hm in "yY":
            config_file = {
                "use_config": True,
                "ipaddress": ipaddress,
                "user_login": {
                    "username": username,
                    "pw": password
                }
            }
            return config_file
        else:
            config_file = {
                "use_config": False
            }
            return config_file


def write_config(appname, media_server_name, config_file):
    print("Writing config file.")
    if media_server_name == "Jellyfin":
        username = json.loads(config_file.get("user_login").decode("utf-8")).get("username")
        password = json.loads(config_file.get("user_login").decode("utf-8")).get("pw")
    else:
        username = config_file.get("user_login").get("username")
        password = config_file.get("user_login").get("pw")
    ipaddress = config_file.get("ipaddress")
    with open("{}/{}.config.json".format(user_cache_dir(appname),
                                         media_server_name.lower()), "w") as output:
        stuff = {
            "username": username,
            "password": password,
            "server": ipaddress
        }
        json.dump(stuff, output)


def test_auth(appname, version, media_server_name, media_server, config_file, auth_header):
    print("Testing {} connection ...".format(media_server_name))
    if media_server_name == "Jellyfin":
        config_file["user_login"] = json.dumps(config_file.get("user_login")).encode("utf-8")
    authorization = requests.post("{}{}/Users/AuthenticateByName"
                                  .format(config_file.get("ipaddress"), media_server),
                                  data=config_file.get("user_login"),
                                  headers=auth_header)
    if authorization.status_code == 200:
        green_print("Connection successfully established!")
        if media_server_name == "Emby":
            request_header = {
                "X-Application": "{}/{}".format(appname, version),
                "X-Emby-Token": authorization.json().get("AccessToken")
            }
        elif media_server_name == "Jellyfin":
            request_header = {
                "X-Application": "{}/{}".format(appname, version),
                "X-Mediabrowser-Token": authorization.json().get("AccessToken")
            }
        user_id = authorization.json().get("User").get("Id")
        session_info = authorization.json().get("SessionInfo")
        return True, True, config_file, request_header, user_id, session_info
    else:
        print("There seems to be some issues connecting to your media-server.\n"
              "    status_code: {}\n [1] Do you want to recreate the config file?\n [E] Exit.\n: "
              .format(authorization.status_code), end="")
        ohoh = get_keypress("1Ee")
        if ohoh == "1":
            config_file = {
                "use_config": False
            }
            config_file, connected, request_header, user_id, session_info = \
                configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header)
            return False, connected, config_file, request_header, user_id, session_info
        else:
            exit()


def configure_new_login(appname, version, media_server_name, media_server, config_file, auth_header):
    username = input("Please enter your {} username: ".format(media_server_name))
    password = input("Please enter your {} password: ".format(media_server_name))
    if " " in username or " " in password:
        print("Make sure to not include any spaces!")
        return False, False, False, False, False
    print("Do you want to confirm your input?\n  (Y)es / (N)o\n: ", end="")
    bored = get_keypress("yYNn")
    if bored in "yY":
        config_file = {
            "use_config": True,
            "ipaddress": config_file.get("ipaddress"),
            "user_login": {
                "username": username,
                "pw": password
            }
        }
        func_succ, connected, config_file, request_header, user_id, session_info = \
            test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
        write_config(appname, media_server_name, config_file)
        return True, config_file, connected, request_header, user_id, session_info
    else:
        connected = True
        request_header = "null"
        user_id = "null"
        session_info = "null"
        return False, config_file, connected, request_header, user_id, session_info


def configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header):
    print("Searching for local media-servers...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.settimeout(2.0)
    broadcast_address = ('255.255.255.255', 7359)
    sock.sendto('who is EmbyServer?'.encode("utf-8"), broadcast_address)
    sock.settimeout(4.0)
    try:
        data = sock.recv(4096)
        data = json.loads(data.decode('utf-8'))
        ipaddress = data['Address']
        print("Is the media-server at the following address the correct one?\n \"{}\"\n (Y)es / (N)o\n: "
              .format(ipaddress), end="")
        answer = get_keypress("yYNn")
        if answer in "yY":
            if "http" not in ipaddress:
                ipaddress = "http://{}".format(ipaddress)
            ipaddress = ipaddress.rstrip("/")
        elif answer in "nN":
            ipaddress = input('Please specify the IP-Address manually\n'
                              '(don\'t forget to add ports if not running on 80/443.)\n: ')
            if "http" not in ipaddress:
                ipaddress = "http://{}".format(ipaddress)
            ipaddress = ipaddress.rstrip("/")
    except socket.timeout:
        ipaddress = input(
            'Couldn\'t find any local media-servers.\nIf your server is dockerized make sure to make it uses the host '
            'network.\n'
            'Or just specify the IP-Address manually'
            '(don\'t forget to add ports if not running on 80/443.)\n: ')
        if "http" not in ipaddress:
            ipaddress = "http://{}".format(ipaddress)
        ipaddress = ipaddress.rstrip("/")
    config_file["ipaddress"] = ipaddress
    if config_file["use_config"]:
        print("Do you want to connect with the following user?\n  {}-username: {}\n  (Y)es / (N)o\n: "
              .format(media_server_name.lower(), config_file.get("user-login").get("username")), end="")
        hungry = get_keypress("yYNn")
        if hungry in "yY":
            func_succ = False
            while not func_succ:
                func_succ, connected, request_header, user_id, session_info = \
                    test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
    func_succ = False
    while not func_succ:
        func_succ, config_file, connected, request_header, user_id, session_info = \
            configure_new_login(appname, version, media_server_name, media_server, config_file, auth_header)
    return config_file, connected, request_header, user_id, session_info


def check_information(appname, version):
    print("What kind of server do you want to stream from?\n [1] Emby\n [2] Jellyfin\n: ", end="")
    media_server = get_keypress("12")
    if media_server == "1":
        media_server = "/emby"
        media_server_name = "Emby"
        auth_header = {"Authorization": 'Emby UserId="", Client="Emby Theater", Device="{}", DeviceId="lol", '
                                        'Version="{}", Token="L"'.format(appname, version)}
    else:
        media_server = ""
        media_server_name = "Jellyfin"
        auth_header = {
            "X-Emby-Authorization": 'Emby UserId="", Client="Emby Theater", Device="{}", DeviceId="lol", '
                                    'Version="{}", Token="L"'.format(appname, version),
            "Content-Type": "application/json"}
    if not os.path.isdir(user_cache_dir(appname)):
        os.makedirs(user_cache_dir(appname))
        config_file = {
            "use_config": False
        }
        config_file, connected, request_header, user_id, session_info = \
            configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header)
        head_dict = {
            "media_server_name": media_server_name,
            "media_server": media_server,
            "config_file": config_file,
            "auth_header": auth_header,
            "request_header": request_header,
            "user_id": user_id
        }
    elif not os.path.isfile("{}/{}.config.json".format(user_cache_dir(appname),
                                                       media_server_name.lower())):
        config_file = {
            "use_config": False
        }
        config_file, connected, request_header, user_id, session_info = \
            configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header)
        head_dict = {
            "media_server_name": media_server_name,
            "media_server": media_server,
            "config_file": config_file,
            "auth_header": auth_header,
            "request_header": request_header,
            "user_id": user_id,
            "session_info": session_info
        }
    else:
        print("Configuration files found!")
        config_file = read_config(appname, media_server_name)
        if not config_file.get("use_config"):
            config_file, connected, request_header, user_id, session_info = \
                configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header)
        else:
            func_succ = False
            while not func_succ:
                func_succ, connected, config_file,  request_header, user_id, session_info = \
                    test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
        if not connected:
            config_file, connected, request_header, user_id, session_info = \
                configure_new_server(appname, version, media_server_name, media_server, config_file, auth_header)
        head_dict = {
            "media_server_name": media_server_name,
            "media_server": media_server,
            "config_file": config_file,
            "auth_header": auth_header,
            "request_header": request_header,
            "user_id": user_id,
            "session_info": session_info
        }
    return head_dict

# This part of puddler asks the user for their account details, emby/jellyfin address and writes the config files.
# returns (hopefully) a dictionary containing: ip_address, user_id, a request_header (with token...) and if emby or jf
import os.path
import uuid
import requests
import json
import socket
from appdirs import *

global connected
connected = None


def green_print(text):
    print("\033[92m{}\033[00m".format(text))


def blue_print(text):
    print("\033[96m{}\033[00m".format(text))


def red_print(text):
    print("\033[91m{}\033[00m".format(text))


# Get key presses without the need to push enter
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
        try:
            data = json.load(config)
            ipaddress = data["server"]
            username = data["username"]
            password = data["password"]
            access_key = data["access_key"]
            user_id = data["user_id"]
            device_id = data["device_id"]
        except:
            print("Couldn't read the existing config file.")
            config_file = {
                "use_config": False,
                "app_auth": {
                    "device_id": str(uuid.uuid4())
                }
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
                },
                "app_auth": {
                    "access_key": access_key,
                    "user_id": user_id,
                    "device_id": device_id
                }
            }
            return config_file
        else:
            config_file = {
                "use_config": False,
                "app_auth": {
                    "device_id": str(uuid.uuid4())
                }
            }
            return config_file


def write_config(appname, media_server_name, config_file):
    if media_server_name == "Jellyfin":
        username = json.loads(config_file.get("user_login").decode("utf-8")).get("username")
        password = json.loads(config_file.get("user_login").decode("utf-8")).get("pw")
        access_key = config_file.get("app_auth").get("access_key")
        user_id = config_file.get("app_auth").get("user_id")
        device_id = config_file.get("app_auth").get("device_id")
    else:
        username = config_file.get("user_login").get("username")
        password = config_file.get("user_login").get("pw")
        access_key = config_file.get("app_auth").get("access_key")
        user_id = config_file.get("app_auth").get("user_id")
        device_id = config_file.get("app_auth").get("device_id")
    ipaddress = config_file.get("ipaddress")
    with open("{}/{}.config.json".format(user_cache_dir(appname),
                                         media_server_name.lower()), "w") as output:
        stuff = {
            "username": username,
            "password": password,
            "server": ipaddress,
            "access_key": access_key,
            "user_id": user_id,
            "device_id": device_id
        }
        json.dump(stuff, output)
    print("Saved to config file...")


def test_auth(appname, version, media_server_name, media_server, config_file, auth_header):
    global connected
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
            auth_header = {
                "Authorization": 'Emby UserId="{}", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                 'Version="{}", Token="{}"'
                    .format(authorization.json().get("SessionInfo").get("UserId"), appname, config_file.get("app_auth")
                            .get("device_id"), version, authorization.json().get("AccessToken"))}
        else:
            request_header = {
                "X-Application": "{}/{}".format(appname, version),
                "X-Emby-Token": authorization.json().get("AccessToken")
            }
            auth_header = {
                "X-Emby-Authorization": 'Emby UserId="{}", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                        'Version="{}", Token="{}"'
                    .format(authorization.json().get("SessionInfo").get("UserId"), appname, config_file.get("app_auth")
                            .get("device_id"), version, authorization.json().get("AccessToken")),
                "Content-Type": "application/json"}
        config_file["app_auth"] = {
            "user_id": authorization.json().get("User").get("Id"),
            "access_key": authorization.json().get("AccessToken"),
            "device_id": config_file.get("app_auth").get("device_id")
        }
        session_id = authorization.json().get("SessionInfo").get("Id")
        connected = True
        return config_file, request_header, auth_header, session_id
    else:
        print("There seems to be some issues connecting to your media-server.\n"
              "    status_code: {}\n [1] Do you want to recreate the config file?\n [E] Exit.\n: "
              .format(authorization.status_code), end="")
        return "" "" "" ""


def configure_new_login(media_server_name, config_file):
    def repeatable():
        username = input("Please enter your {} username: ".format(media_server_name))
        password = input("Please enter your {} password: ".format(media_server_name))
        return username, password

    bored = None
    while not bored:
        username, password = repeatable()
        if " " in username or " " in password:
            print("Make sure to not include any spaces!")
            continue
        print("Do you want to confirm your input?\n  (Y)es / (N)o\n: ", end="")
        if get_keypress("yYNn") in "yY":
            bored = "bruh"
    config_file["user_login"] = {
        "username": username,
        "pw": password
    }
    config_file["app_auth"] = {
        "user_id": "",
        "device_id": config_file.get("app_auth").get("device_id")
    }
    return config_file


def configure_new_server(config_file):
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
    config_file = {
        "use_config": True,
        "ipaddress": ipaddress,
        "app_auth": {
            "device_id": config_file.get("app_auth").get("device_id")
        }
    }
    return config_file


def check_information(appname, version):
    global connected
    print("What kind of server do you want to stream from?\n [1] Emby\n [2] Jellyfin\n: ", end="")
    media_server = get_keypress("12")
    new_uuid = str(uuid.uuid4())
    config_file = {
        "app_auth": {
            "device_id": new_uuid
        }
    }
    if media_server == "1":
        media_server = "/emby"
        media_server_name = "Emby"
        auth_header = {"Authorization": 'Emby UserId="", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                        'Version="{}", Token="L"'.format(appname, new_uuid, version)}
    else:
        media_server = ""
        media_server_name = "Jellyfin"
        auth_header = {
            "X-Emby-Authorization": 'Emby UserId="", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                    'Version="{}", Token="L"'.format(appname, new_uuid, version),
            "Content-Type": "application/json"}
    if not os.path.isdir(user_cache_dir(appname)):
        os.makedirs(user_cache_dir(appname))
        config_file = configure_new_server(config_file)
        config_file = configure_new_login(media_server_name, config_file)
        while not connected:
            config_file, request_header, auth_header, session_id = \
                test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
            if not connected:
                ohoh = get_keypress("1Ee")
                if ohoh == "1":
                    config_file = configure_new_login(media_server_name, config_file)
                else:
                    exit()
            else:
                write_config(appname, media_server_name, config_file)
    elif not os.path.isfile("{}/{}.config.json".format(user_cache_dir(appname),
                                                       media_server_name.lower())):
        config_file = configure_new_server(config_file)
        config_file = configure_new_login(media_server_name, config_file)
        while not connected:
            config_file, request_header, auth_header, session_id = \
                test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
            if not connected:
                ohoh = get_keypress("1Ee")
                if ohoh == "1":
                    config_file = configure_new_login(media_server_name, config_file)
                else:
                    exit()
            else:
                write_config(appname, media_server_name, config_file)
    else:
        print("Configuration files found!")
        config_file = read_config(appname, media_server_name)
        if not config_file.get("use_config"):
            config_file = configure_new_server(config_file)
            config_file = configure_new_login(media_server_name, config_file)
            while not connected:
                config_file, request_header, auth_header, session_id = \
                    test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
                if not connected:
                    ohoh = get_keypress("1Ee")
                    if ohoh == "1":
                        config_file = configure_new_login(media_server_name, config_file)
                    else:
                        exit()
                else:
                    write_config(appname, media_server_name, config_file)
        else:
            if media_server_name == "Emby":
                auth_header = {
                    "Authorization": 'Emby UserId="{}", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                     'Version="{}", Token="{}"'
                        .format(config_file.get("app_auth").get("user_id"), appname, config_file.get("app_auth")
                                .get("device_id"), version, config_file.get("app_auth").get("access_key"))
                }
            else:
                auth_header = {
                    "X-Emby-Authorization": 'Emby UserId="{}", Client="Emby Theater", Device="{}", DeviceId="{}", '
                                            'Version="{}", Token="{}"'
                        .format(config_file.get("app_auth").get("user_id"), appname, config_file.get("app_auth")
                                .get("device_id"), version, config_file.get("app_auth").get("access_key")),
                    "Content-Type": "application/json"}
            request_header = {
                "X-Application": "{}/{}".format(appname, version),
                "X-Emby-Token": config_file.get("app_auth").get("access_key")
            }
    while not connected:
        print("Testing {} connection ...".format(media_server_name))
        try:
            session_id = requests.get("{}{}/Sessions?DeviceId={}"
                                      .format(config_file.get("ipaddress"), media_server, config_file.get("app_auth")
                                .get("device_id")), headers=auth_header).json()[0].get("PlayState").get("Id")
        except requests.exceptions.JSONDecodeError:
            print("Something failed, re-authenticating...")
            config_file, request_header, auth_header, session_id = \
                test_auth(appname, version, media_server_name, media_server, config_file, auth_header)
            write_config(appname, media_server_name, config_file)
        finally:
            green_print("Connection successfully reestablished!")
            connected = True
    head_dict = {
        "media_server_name": media_server_name,
        "media_server": media_server,
        "config_file": config_file,
        "auth_header": auth_header,
        "request_header": request_header,
        "session_id": session_id
    }
    return head_dict

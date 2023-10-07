import bz2
import hashlib
import os
import subprocess
import sys
import platform

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
import UnityPy

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
ENCTYPTED_DIR = os.path.join(os.path.dirname(__file__), "encrypted")
DECRYPTED_DIR = os.path.join(os.path.dirname(__file__), "decrypted")
MAX_THREADS = 4

system = platform.system().lower()
arch = platform.architecture()

XOR_BIN = f"./bin/{system}/{arch[0]}/xor"

if system == "windows":
    XOR_BIN += ".exe"

for dir in [ASSETS_DIR, ENCTYPTED_DIR, DECRYPTED_DIR]:
    if not os.path.exists(dir):
        os.mkdir(dir)

def console_log(text):
    sys.stdout.write(f"[WOG DUMP] {text}")
    sys.stdout.flush()


def download_weaponlist():
    if os.path.exists(f"{ASSETS_DIR}/spider_gen.unity3d"):
        current_size = os.path.getsize(f"{ASSETS_DIR}/spider_gen.unity3d")
        server_size = int(requests.head(
            "https://data1eu.ultimate-disassembly.com/uni2018/spider/spider_gen.unity3d").headers["Content-Length"])
        console_log(
            f"Current size: {current_size} | Server size: {server_size}\n")
        if current_size == server_size:
            console_log("Asset up to date\n")
            return
        else:
            console_log("Asset not up to date\n")
    console_log("Downloading asset\n")
    r = requests.get(
        "https://data1eu.ultimate-disassembly.com/uni2018/spider/spider_gen.unity3d", stream=True)
    if r.status_code == 200:
        with open(f"{ASSETS_DIR}/spider_gen.unity3d", "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)


def unpack_weaponlist():
    weapon_list = []
    env = UnityPy.load(f"{ASSETS_DIR}/spider_gen.unity3d")
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            if data.name == "new_banners":
                with open("weapons.txt", "w") as f:
                    text = data.text.replace("\r", "")
                    lines = text.split("\n")
                    # remove empty lines
                    lines = [line for line in lines if line != ""]
                    # remove lines starting with #
                    lines = [line for line in lines if not line.startswith("#")]
                    # remove .png and add to list
                    for line in lines:
                        weapon_list.append(line.split(".png")[0])
                    #  remove blacklisted
                    weapon_list = remove_blacklisted(weapon_list)
                    text = "\n".join(weapon_list)
                    f.write(text)
    console_log("Unpacked weapons.txt\n")


def remove_blacklisted(weapon_list):
    black_list = ["shooting_01", "shooting_02", "shooting_03", "shooting_04", "shooting_05",
                  "shooting_06", "shooting_07", "shooting_08", "shooting_09", "shooting_10"]
    # OMG unreleased guns
    weapon_black_list = ["hk_g28", "drag_racing",
                         "tac_50", "zis_tmp", "groza_1", "glock_19x", "cat_349f"]

    weapon_list = [weapon for weapon in weapon_list if not weapon in black_list]
    weapon_list = [weapon for weapon in weapon_list if not weapon in weapon_black_list]
    return weapon_list


def get_weapon_list():
    with open("weapons.txt", "r") as f:
        return f.read().split("\n")


def get_key(asset_name):
    data = f"query=3&model={asset_name}&mode=FIELD_STRIP&need_details=1&ver=2.2.1z5&uver=2019.2.18f1&dev=e35c060a502dd9fdee3bfa107ab0cc24477f6a1a&session=35&id=5390315&time=169611572"
    headers = {
        'Content-Type': 'application/octet-stream',
        'User-Agent': 'UnityPlayer/2019.2.18f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)',
        'Accept-Encoding': 'identity',
        'Accept': '*/*',
        'X-Unity-Version': '2019.2.18f1',
    }
    # request -> gzip
    data = bz2.compress(data.encode())
    # gzip -> bytes
    data = BytesIO(data)
    # add 4 bytes - length of the data
    length = len(data.getbuffer())
    data = length.to_bytes(4, "little") + data.getbuffer()
    headers['Content-Length'] = str(len(data))
    # send request
    r = requests.put(
        "https://eu1.ultimate-disassembly.com/v/query2018.php?soc=steam", data=data, headers=headers)
    # remove 4 bytes from the beginning of the response
    r = r.content[4:]
    # gzip -> str
    r = bz2.decompress(r).decode()
    # get key
    try:
        key = r.split("sync=")[1].split("&")[0]
    except IndexError:
        key = None
    return key


def dump_keys_threaded(weapon_list: list):
    keys = {}

    def get_key_threaded(asset_name):
        key = get_key(asset_name)
        console_log(
            f"Gettings keys {weapon_list.index(asset_name) + 1}/{len(weapon_list)}\r")
        keys.update({asset_name: key})

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for weapon in weapon_list:
            executor.submit(get_key_threaded, weapon)

    with open("keys.txt", "w") as f:
        for weapon in weapon_list:
            key = keys[weapon]
            if key is not None:
                f.write(f"{weapon} {key}\n")
    console_log("\n")


def download_file(url, filename, current, total):
    r = requests.get(url, stream=True)
    file_size = int(r.headers["Content-Length"])
    if r.status_code != 200:
        console_log(f"[{current}/{total}] Error downloading {filename}                  \r")
        return
    with open(filename, "wb") as f:
        for chunk in r.iter_content(1024):
            console_log(
                f"[{current}/{total}] [{round(f.tell()/file_size*100, 2)}% | {round(f.tell()/1024/1024, 2)}MB/{round(file_size/1024/1024, 2)}MB] Downloading {filename} \r")
            f.write(chunk)

    console_log(f"[{current}/{total}] Downloaded {filename}                                     \r")


def get_asset_size(asset):
    r = requests.head(f"https://data1eu.ultimate-disassembly.com/uni2018/{asset}.unity3d")
    return int(r.headers["Content-Length"])


def check_for_updates_threaded(weapon_list):
    to_download = []


    def check_for_updates(asset):
        if not os.path.exists(f"{ASSETS_DIR}/{asset}.unity3d"):
            to_download.append(asset)
            return
        current_size = os.path.getsize(f"{ASSETS_DIR}/{asset}.unity3d")
        server_size = get_asset_size(asset)
        console_log(
            f"Checking for updates {weapon_list.index(asset) + 1}/{len(weapon_list)}\r")
        if current_size != server_size:
            to_download.append(asset)

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for weapon in weapon_list:
            executor.submit(check_for_updates, weapon)

    return to_download


def download_all(weapon_list):
    to_download = check_for_updates_threaded(weapon_list)
    total_downloads = len(to_download)
    for asset, i in zip(to_download, range(total_downloads)):
        url = f"https://data1eu.ultimate-disassembly.com/uni2018/{asset}.unity3d"
        filename = f"{ASSETS_DIR}/{asset}.unity3d"
        download_file(url, filename, i + 1, total_downloads)
    console_log("Downloaded all assets\n")


def load_keys():
    keys = {}
    with open("keys.txt", "r") as f:
        lines = f.readlines()
    for line in lines:
        asset_name = line.split(" ")[0]
        key = line.split(" ")[1].replace("/n", "").strip()
        keys.update({asset_name: key})
    return keys


def decrypt_all(keys):
    assets = os.listdir(ASSETS_DIR)
    assets.remove("spider_gen.unity3d")
    for asset in assets:
        key = keys[asset.split(".")[0]] + "World of Guns: Gun Disassembly"
        key = hashlib.md5(key.encode()).hexdigest()
        console_log(
            f"Unpacking and decrypting {assets.index(asset) + 1}/{len(assets)}\r")
        env = UnityPy.load(f"{ASSETS_DIR}/{asset}")
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                with open(f"{ENCTYPTED_DIR}/{data.name}.bytes", "wb") as f:
                    f.write(bytes(data.script))
                # # decrypt // usage: xor <input> <key> <output>
                subprocess.call(
                    [XOR_BIN, f"{ENCTYPTED_DIR}/{data.name}.bytes", key, f"{DECRYPTED_DIR}/{data.name}.unity3d"])


def main():
    download_weaponlist()
    unpack_weaponlist()
    weapon_list = get_weapon_list()
    asnwer = input("[WOG DUMP] Update decrypting keys? (y/n): ")
    if asnwer.lower() == "y":
        dump_keys_threaded(weapon_list)
    console_log(f"Found {len(weapon_list)} weapons\n")
    asnwer = input("[WOG DUMP] Checking for updates? (y/n): ")
    if asnwer == "y":
        download_all(weapon_list)
    keys = load_keys()
    decrypt_all(keys)
    console_log("Done")


if __name__ == "__main__":
    main()

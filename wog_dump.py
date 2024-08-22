import bz2
import hashlib
import os
import subprocess
import sys
import platform

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import time

import requests
import UnityPy

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "raw")
ENCTYPTED_DIR = os.path.join(os.path.dirname(__file__), "assets", "encrypted")
DECRYPTED_DIR = os.path.join(os.path.dirname(__file__), "assets", "decrypted")
MAX_THREADS = 4

system = platform.system().lower()
arch = platform.machine().lower()

XOR_BIN = f"./bin/{system}/{arch}/xor"

if system == "windows":
    XOR_BIN += ".exe"

for dir in [ASSETS_DIR, ENCTYPTED_DIR, DECRYPTED_DIR]:
    if not os.path.exists(dir):
        os.mkdir(dir)


def console_log(text):
    sys.stdout.write(f"[WOG DUMP] {text}")
    sys.stdout.flush()


class WogDumper:
    def __init__(self, assets_dir, decrypted_dir, encrypted_dir, xor_bin, max_threads):
        self.ASSETS_DIR = assets_dir
        self.DECRYPTED_DIR = decrypted_dir
        self.ENCRYPTED_DIR = encrypted_dir
        self.XOR_BIN = xor_bin
        self.MAX_THREADS = max_threads
        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
        self.keys = {}
        self.weapon_list = []
        self.session_id, self.account_id = self.get_session()

    def download_weaponlist(self):
        if os.path.exists(f"{self.ASSETS_DIR}/spider_gen.unity3d"):
            current_size = os.path.getsize(f"{self.ASSETS_DIR}/spider_gen.unity3d")
            server_size = int(requests.head("https://data1eu.ultimate-disassembly.com/uni2018/spider/spider_gen.unity3d").headers["Content-Length"])
            console_log(f"Current size: {current_size} | Server size: {server_size}\n")
            if current_size == server_size:
                console_log("Asset up to date\n")
                return
            else:
                console_log("Asset not up to date\n")
        console_log("Downloading asset\n")
        r = requests.get("https://data1eu.ultimate-disassembly.com/uni2018/spider/spider_gen.unity3d", stream=True)
        if r.status_code == 200:
            with open(f"{self.ASSETS_DIR}/spider_gen.unity3d", "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

    def unpack_weaponlist(self):
        weapon_list = []
        env = UnityPy.load(f"{self.ASSETS_DIR}/spider_gen.unity3d")
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                if data.name == "new_banners":
                    text = data.text.replace("\r", "")
                    lines = text.split("\n")
                    lines = [line for line in lines if line != ""]
                    lines = [
                        line for line in lines if not line.startswith("#")]
                    for line in lines:
                        weapon_list.append(line.split(".png")[0])
                    weapon_list = self.remove_blacklisted(weapon_list)
                    self.weapon_list = weapon_list
        console_log("Unpacked weapons.txt\n")

    def remove_blacklisted(self, weapon_list):
        weapon_black_list = ["hk_g28", "drag_racing", "tac_50", "zis_tmp", "groza_1", "glock_19x", "cat_349f",
                             "fnx_45", "korth_super_sport_alx", "canik_tp9"]

        weapon_list = [weapon for weapon in weapon_list if not weapon.startswith("shooting_")]
        weapon_list = [weapon for weapon in weapon_list if weapon not in weapon_black_list]
        return weapon_list

    def send_request(self, data):
        headers = {
            'Content-Type': 'application/octet-stream',
            'User-Agent': 'UnityPlayer/2022.3.23f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Accept-Encoding': 'identity',
            'Accept': '*/*',
            'X-Unity-Version': '2022.3.23f1',
        }
        data = bz2.compress(data.encode())
        data = BytesIO(data)
        length = len(data.getbuffer())
        data = length.to_bytes(4, "little") + data.getbuffer()
        headers['Content-Length'] = str(len(data))
        r = requests.put(
            "https://eu1.ultimate-disassembly.com/v/query2018.php?soc=steam", data=data, headers=headers)
        r = r.content[4:]
        r = bz2.decompress(r).decode()
        return r

    def get_session(self):
        console_log("Getting session\n")
        data = f"query=2&client=googleplay&user=Guest&ver=2.2.2v5&uver=2022.3.23f1&dev=e35c060a502dd9fdee3bfa107ab0cc24477f6a1a&session=0&id=0&time={time.time()}&platform=&hash=01c93ed662aaf8fa8faee16748a4121a"
        r = self.send_request(data)
        session_id = r.split("session=")[1].split("&")[0]
        acc_id = r.split("acc_id=")[1].split("&")[0]
        console_log(f"Session ID: {session_id} | Account ID: {acc_id}\n")
        return session_id, acc_id

    def get_key(self, asset_name):
        data = f"query=3&model={asset_name}&mode=FIELD_STRIP&need_details=1&ver=2.2.2z5&uver=2022.3.23f1&dev=e35c060a502dd9fdee3bfa107ab0cc24477f6a1a&session={self.session_id}&id={self.account_id}&time={int(time.time())}"
        r = self.send_request(data)
        try:
            key = r.split("sync=")[1].split("&")[0]
        except IndexError:
            console_log(f"Error getting key for {asset_name}\n")
            key = None
        return key

    def get_key_threaded(self, asset_name):
        key = self.get_key(asset_name)
        console_log(f"Gettings keys {self.weapon_list.index(asset_name) + 1}/{len(self.weapon_list)}\r")
        self.keys.update({asset_name: key})


    def dump_keys_threaded(self):
        self.executor = ThreadPoolExecutor(max_workers=self.MAX_THREADS)
        self.executor.map(self.get_key_threaded, self.weapon_list)
        self.executor.shutdown(wait=True)

        with open("keys.txt", "w") as f:
            for weapon in self.weapon_list:
                key = self.keys[weapon]
                if key is not None:
                    f.write(f"{weapon} {key}\n")
        console_log("\n")

    def download_file(self, url, filename, current, total):
        r = requests.get(url, stream=True)
        file_size = int(r.headers["Content-Length"])
        if r.status_code != 200:
            console_log(
                f"[{current}/{total}] Error downloading {filename}                          \r")
            return
        with open(filename, "wb") as f:
            for chunk in r.iter_content(1024):
                console_log(f"[{current}/{total}] [{round(f.tell()/file_size*100, 2)}% | {round(f.tell()/1024/1024, 2)}MB/{round(file_size/1024/1024, 2)}MB] Downloading {filename} \r")
                f.write(chunk)
        console_log(
            f"[{current}/{total}] Downloaded {filename}                                     \r")

    def get_asset_size(self, asset):
        r = requests.head(f"https://data1eu.ultimate-disassembly.com/uni2018/{asset}.unity3d")
        return int(r.headers["Content-Length"])

    def check_for_updates_threaded(self, weapon_list):
        to_download = []

        def check_for_updates(asset):
            console_log(f"Checking for updates {weapon_list.index(asset) + 1}/{len(weapon_list)}\r")
            if not os.path.exists(f"{self.ASSETS_DIR}/{asset}.unity3d"):
                to_download.append(asset)
                return
            current_size = os.path.getsize(
                f"{self.ASSETS_DIR}/{asset}.unity3d")
            server_size = self.get_asset_size(asset)
            if current_size != server_size:
                to_download.append(asset)

        self.executor = ThreadPoolExecutor(max_workers=self.MAX_THREADS)
        self.executor.map(check_for_updates, weapon_list)
        self.executor.shutdown(wait=True)

        return to_download

    def download_and_decrypt_all(self):
        to_download = self.check_for_updates_threaded(self.weapon_list)
        total_downloads = len(to_download)
        for asset, i in zip(to_download, range(total_downloads)):
            url = f"https://data1eu.ultimate-disassembly.com/uni2018/{asset}.unity3d"
            filename = f"{self.ASSETS_DIR}/{asset}.unity3d"
            self.download_file(url, filename, i + 1, total_downloads)
            self.decrypt_single(self.keys, f"{asset}.unity3d")
        console_log("Downloaded and decrypted all assets\n")

    def load_keys(self):
        with open("keys.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            asset_name = line.split(" ")[0]
            key = line.split(" ")[1].replace("/n", "").strip()
            self.keys.update({asset_name: key})

    def decrypt_all(self, keys):
        assets = os.listdir(self.ASSETS_DIR)
        assets.remove("spider_gen.unity3d")
        for asset in assets:
            key = keys[asset.split(".")[0]] + "World of Guns: Gun Disassembly"
            key = hashlib.md5(key.encode()).hexdigest()
            console_log(
                f"Unpacking and decrypting {assets.index(asset) + 1}/{len(assets)}\r")
            env = UnityPy.load(f"{self.ASSETS_DIR}/{asset}")
            for obj in env.objects:
                if obj.type.name == "TextAsset":
                    data = obj.read()
                    if os.path.exists(f"{self.DECRYPTED_DIR}/{data.name}.unity3d"):
                        if os.path.getsize(f"{self.ENCRYPTED_DIR}/{data.name}.bytes") == data.script.nbytes:
                            console_log(
                                f"Already decrypted - {data.name}.unity3d\n")
                            continue
                    with open(f"{self.ENCRYPTED_DIR}/{data.name}.bytes", "wb") as f:
                        f.write(bytes(data.script))
                    subprocess.call(
                        [self.XOR_BIN, f"{self.ENCRYPTED_DIR}/{data.name}.bytes", key, f"{self.DECRYPTED_DIR}/{data.name}.unity3d"])

    def decrypt_single(self, keys, asset):
        key = keys[asset.split(".")[0]] + "World of Guns: Gun Disassembly"
        key = hashlib.md5(key.encode()).hexdigest()
        env = UnityPy.load(f"{self.ASSETS_DIR}/{asset}")
        for obj in env.objects:
            if obj.type.name == "TextAsset":
                data = obj.read()
                if os.path.exists(f"{self.DECRYPTED_DIR}/{data.name}.unity3d"):
                    if os.path.getsize(f"{self.ENCRYPTED_DIR}/{data.name}.bytes") == data.script.nbytes:
                        console_log(
                            f"Already decrypted - {data.name}.unity3d\n")
                        return
                with open(f"{self.ENCRYPTED_DIR}/{data.name}.bytes", "wb") as f:
                    f.write(bytes(data.script))
                subprocess.call(
                    [self.XOR_BIN, f"{self.ENCRYPTED_DIR}/{data.name}.bytes", key, f"{self.DECRYPTED_DIR}/{data.name}.unity3d"])
                return

    def start(self):
        self.download_weaponlist()
        self.unpack_weaponlist()
        keys_exist = os.path.exists("keys.txt") and os.path.getsize("keys.txt") > 0
        answer = input("[WOG DUMP] Update decrypting keys? (y/n): ")
        if answer.lower() == "y" or keys_exist:
            self.dump_keys_threaded()
        console_log(f"Found {len(self.weapon_list)} weapons \n")
        answer = input("[WOG DUMP] Checking for updates? (y/n): ")
        self.load_keys()
        if answer.lower() == "y":
            self.download_and_decrypt_all()
        console_log("Done")


if __name__ == "__main__":
    wog_dumper = WogDumper(assets_dir=ASSETS_DIR, decrypted_dir=DECRYPTED_DIR,
                           encrypted_dir=ENCTYPTED_DIR, xor_bin=XOR_BIN, max_threads=MAX_THREADS)
    wog_dumper.start()
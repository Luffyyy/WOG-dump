# 🔫 World of Guns model dumper 

![World of Guns](https://cdn.cloudflare.steamstatic.com/steam/apps/262410/library_hero.jpg)

### 📙 Description
This script allows you to download, decrypt and unpack models from the game [World of Guns: Gun Disassembly](https://store.steampowered.com/app/262410/World_of_Guns_Gun_Disassembly/)

### 🔗 Requirements
- Python 3.10+ 
- C compiler (for `xor.c`)
- [AssetStudio](https://github.com/Perfare/AssetStudio) (for unpacking assets)

### 🪄 How it works
1. Download asset with texture atlas and filter weapons from it
2. Download key for decryption
3. Decrypts and unpacks models
4. Ez profit

### 🧑‍🏭 Usage
1. Clone repository - `git clone https://github.com/hampta/WOG-dump`
2. Go to dirictory - `cd WOG-dump`
3. Install requirements - `pip install -r requirements.txt`
4. Run - `python wog_dump.py`
5. Unpack assets in `decrypted` dir by [AssetStudio](https://github.com/Perfare/AssetStudio)

### ➕ Addtional
Use xor: `xor <encrypted_file> <key> <output_file>`

Convert Unity normal maps: `python convert_normal_map.py <path>`

### 🫂 Special thanks
[DeadZoneGarry](https://github.com/DeadZoneLuna) - helping with decryption

[Noble Empire Corp.](https://noble-empire.com/news.php) - game and assets
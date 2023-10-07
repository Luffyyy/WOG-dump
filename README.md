# 🔫 World of Guns model dumper 

![World of Guns](https://cdn.cloudflare.steamstatic.com/steam/apps/262410/library_hero.jpg)

## 📙 Description
This script allows you to download, decrypt and unpack models from the game [World of Guns: Gun Disassembly](https://store.steampowered.com/app/262410/World_of_Guns_Gun_Disassembly/)

## 🔗 Requirements
- Python 3.10+ 
- [AssetStudio](https://github.com/Perfare/AssetStudio) - for unpacking assets
- C compiler - for compile [`xor.c`](https://github.com/hampta/WOG-dump/blob/main/xor.c) (optional)

## 🪄 How it works
1. Download asset with texture atlas and filter weapons from it
2. Download key for decryption
3. Decrypts and unpacks models
4. Ez profit

## 🧑‍🏭 Usage
**Windows**
```bash
git clone https://github.com/hampta/WOG-dump    # Clone repository
cd WOG-dump                                     # Go to directory
pip install -r requirements.txt                 # Install requirements
python wog_dump.py                              # Run
```

**Linux**
```bash
git clone https://github.com/hampta/WOG-dump    # Clone repository
cd WOG-dump                                     # Go to directory
pip3 install -r requirements.txt                # Install requirements
python3 wog_dump.py                             # Run
```

- Unpack assets in `decrypted` dir with [AssetStudio](https://github.com/Perfare/AssetStudio)

## ➕ Addtional
Use xor decryptor: 
```bash
# Windows 64 bit
./bin/windows/64bit/xor.exe <encrypted_file> <key> <output_file>

# Windows 32 bit
./bin/windows/32bit/xor.exe <encrypted_file> <key> <output_file>

# Linux
./bin/linux/64bit/xor <encrypted_file> <key> <output_file>
```

Convert Unity normal maps: 
```bash
# Windows
python convert_normal_map.py <path> 

#Linux 
python3 convert_normal_map.py <path> 
```

## 🫂 Special thanks
[DeadZoneGarry](https://github.com/DeadZoneLuna) - helping with decryption

[Noble Empire Corp.](https://noble-empire.com/news.php) - game and assets
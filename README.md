# Save Game Syncer with Owncloud/Nextcloud for Linux
A little script which syncs (uploads and downloads) savegames for common linux games.

## Currently supported Games
* Celeste
* Deponia1
* Deponia2
* Deponia3
* Guacamelee
* Hacknet
* HollowKnight
* HunieCamStudio
* HuniePop
* Skullgirls
* SuperHexagon
* SuperMeatBoy

## Configuration
You need a configuration file in your home directory
Generate one with the setup wizard:
```bash
savegame_sync.sh -s
```

Or alternatively create your own
```bash
user$ mkdir .savegame_sync
user$ vim .savegame_sync/config.cfg
```
with the following content
```bash
CLOUD_DOMAIN="your.domain.name" # the domain name of your nextcloud/owncloud
CLOUD_URL_PATH="somesubdiretory" # if you installed your owncloud on some subdirectory of your webroot you can add the path here. Can be empty
CLOUD_USER=$YOUR_USERNAME # your Cloud username
CLOUD_PASSWORD="$YOUR_PASSWORD" your Cloud password. If not set, password from standard input
CLOUD_SYNC_DIR="$YOUR_WEBDAV_DIRECTORY" # directory in your owncloud webdav root. Standard configuration is "savegames"
```
If you don't want to use the configuration file, you can start the script wit set variables:
```bash
CLOUD_DOMAIN="your.domain.com" CLOUD_USER=tux savegame_sync.sh -u "$Game1, $Game2"
```


## Usage
Upload the files to your Cloud:
```bash
savegame_sync.sh -u "$Game1, $Game2"
```

Download the files from your Cloud
to the correct location:
```bash
savegame_sync.sh -d "$Game1, $Game2"
```

List all available games:
```bash
savegame_sync.sh -l
```

Wizard for the configuration file:
```bash
savegame_sync.sh -s
```

Show the help message:
```bash
savegame_sync.sh -h
```

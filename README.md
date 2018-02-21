# Save Game Syncer with Owncloud/Nextcloud for Linux
a little script which provides a save game sync for every linux game added implemented

## currently support
* Hollow Knight
* Celeste
* Hacknet
* Deponia1
* Deponia2
* Deponia3
* Skullgirls
* SuperHexagon


## Usage
```bash
savegame_sync.sh -u "$Game1, $Game2"
```
uploads the files to your Cloud
```bash
savegame_sync.sh -d "$Game1, $Game2"
```
Downloads the files from your Cloud
to the correct location
```bash
savegame_sync.sh -l
```
Lists all available games
```bash
savegame_sync.sh -h
```
Shows this help message

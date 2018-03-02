# savegame\_sync
## Save Game Syncer with Owncloud/Nextcloud for Linux
A little script which syncs (uploads and downloads) savegames for common linux games.

## Currently supported Games
* AmnesiaADarkDescent
* Celeste
* Deponia1
* Deponia2
* Deponia3
* Guacamelee
* Hacknet
* Hedgewars
* HollowKnight
* HunieCamStudio
* HuniePop
* OlliOlli
* OlliOlli2
* Quake3
* ShovelKnight
* Skullgirls
* StardewValley
* SuperHexagon
* SuperMeatBoy
* Teeworlds
* TheEndIsNigh

## Configuration
Before you can use the script, you need a configuration file
in your home directory. Generate one with the setup wizard:
```bash
savegame_sync.sh -s [--setup]
```

## Usage
**Caution**: Every Game must be comma seperated white a trailing whitespace after a comma.

Upload the files to your Cloud. If you want to upload all available games, use "all":
```bash
savegame_sync.sh -u [--upload] --games "$Game1, $Game2"
```

Download the files from your Cloud. If you want to download all available games, use "all"
to the correct location:
```bash
savegame_sync.sh -d [--download] --games "$Game1, $Game2"
```

List all available games:
```bash
savegame_sync.sh -l [--list]
```

Wizard for the configuration file:
```bash
savegame_sync.sh -s [--setup]
```

Show the help message:
```bash
savegame_sync.sh -h [--help]
```

Show the program version:
```bash
savegame_sync.sh -v [--version]
```

## ToDos
* save password hashed
* get password from stdin
* use python setup.py instad of Makefile

# savegame\_sync
## Save Game Syncer with Owncloud/Nextcloud for Linux
A little script which syncs (uploads and downloads) savegames for common linux games.

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
## Howto add games
If you miss a game, which is not listed here, just fork the project, add the missing game to the *games.xml* and send an submit request. If you don't know where the savestate of your game is located, check-out [PCGamingWiki](https://pcgamingwiki.com/wiki/Home). Linux savegame location is most probably listed there.

## Currently supported Games
* AmnesiaADarkDescent
* BioshockInfinite
* BitTripRunner
* Celeste
* Deponia1
* Deponia2
* Deponia3
* Doom3
* DungeonDefenders
* DustAnElysianTail
* EnemyTerritoryQuakeWars
* Gish
* Guacamelee
* Hacknet
* Hedgewars
* HollowKnight
* HotlineMiami
* HotlineMiami2
* HunieCamStudio
* HuniePop
* Jamestown
* KatawaShoujo
* Limbo
* MarkOfTheNinja
* NaturalSelection2
* OlliOlli
* OlliOlli2
* OpenArena
* Postal2
* Psychonauts
* Quake3
* Quake4
* Rochard
* Rust
* Shank1
* Shank2
* ShovelKnight
* Skullgirls
* StardewValley
* SuperHexagon
* SuperMeatBoy
* SurgeonSimulator2013
* SwordsAndSoldiers
* Teeworlds
* TheBindingOfIsaacRebirth
* TheEndIsNigh
* Torchlight1
* Torchlight2
* UT2004
* Vessel

## ToDos
* save password hashed
* get password from stdin
* use python setup.py instad of Makefile
* Add parameter to backup old cloudsave and rename it

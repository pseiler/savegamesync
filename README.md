# savegamesync
## Save Game Syncer with Owncloud/Nextcloud for Linux
A little script which syncs (uploads and downloads) savegames for common linux games.
The purpose is to have your savegames (and for some games the configuration) on every device in sync.
The only requirement is, to have an access to an OwnCloud/Nextcloud. It reads the savestate location from
a shipped *games.xml* for every supported game and puts an archive to a configurable location on your Cloud.

## Installation
Make sure you installed **tar**, **gzip**, **pycURL**, **make** and **python 2.7**.
To install savegamesync:
1. Download the tarball
2. Extract it
3. type ``sudo make install``
4. Run savegamesync with all necessary parameters on the command line
5. Enjoy

To uninstall savegamesync just run ``sudo make uninstall`` from the installation directory.

## Configuration
Before you can use the script, you need a configuration file
in your home directory. Generate one with the setup wizard:
```bash
savegamesync -s [--setup]
```

## Usage
**Caution**: Every Game must be comma seperated white a trailing whitespace after a comma.

Upload the files to your Cloud. If you want to upload all available games, use "all":
```bash
savegamesync -u [--upload] --games "$Game1, $Game2"
```

Download the files from your Cloud to the correct location. If you want to download all
 available games, use "all"
```bash
savegamesync -d [--download] --games "$Game1, $Game2"
```

List all available games:
```bash
savegamesync -l [--list]
```

Wizard for the configuration file:
```bash
savegamesync -s [--setup]
```

Show the help message:
```bash
savegamesync -h [--help]
```

Show the program version:
```bash
savegamesync -v [--version]
```
## Howto add games
If you miss a game, which is not listed here, just fork the project, add the missing game to the *games.xml* and send an submit request. If you don't know where the savestate of your game is located, check-out [PCGamingWiki](https://pcgamingwiki.com/wiki/Home). Linux savegame location is most probably listed there.

## Currently supported Games
* 140
* AVirusNamedTom
* AmnesiaADarkDescent
* AmnesiaAMachineForPigs
* AnomalyKorea
* Antichamber
* Aquaria
* Avadon1
* Bastion
* BeatBuddyTaleOfTheGuardians
* BeatHazard
* BeatHazardUltra
* BioshockInfinite
* BitTripPresentsRunner2
* BitTripRunner
* Botanicula
* Braid
* BreachAndClear
* BrokenAge
* BrokenSword1DirectoresCut
* BrokenSword2
* BrokenSword5
* BrütalLegend
* Capsized
* CaveStory+
* Celeste
* Closure
* Cogs
* ContraptionMaker
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
* TheBardsTale
* TheBindingOfIsaacRebirth
* TheBridge
* TheEndIsNigh
* Torchlight1
* Torchlight2
* Trine1
* Trine2
* Trine3
* TrineEnchantedEdition
* UT2004
* Vessel

## ToDos
* save password with a better hash than base64
* use python setup.py instad of Makefile
* Add parameter to backup old cloudsave and rename it
* Add support to copy everything just to a local directory
* consider to use yaml instead of xml

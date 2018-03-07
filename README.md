# savegamesync
## Linux Savegame Syncer with support for local directory and Owncloud/Nextcloud backups
* Create a local copy of all available games to a configurable directory
* Upload your savegames to your Nextcloud/OwnCloud
* Download your savegames from your Nextcloud/ownCloud and put it to the correct game directory automatically
* Preserve old backups in case you accidently overwrite an old savegame
* Add support for a missing game by contributing to a *xml* list

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
Before you can use the script with your cloud, you need a configuration file
in your home directory. Generate one with the setup wizard.
If you want your local backup somewhere other than *${HOME}/savegames* you also
must use the wizard to create a config file:
```bash
savegamesync -s [--setup]
```
## Usage
### Short Options
**Caution**: For every option exists a short option. If you want to use only short options following syntax is also okay:
```bash
savegamesync -bcdpg $Game1 $Game2
```
This copies the backup of the savegame to a local defined folder and uploads it to your cloud. It renames the old file on both destinations (Cloud and local). For more explanation only the long options are listed here.

### Long Options explained
Upload the files to your Cloud. If you want to upload all available games, use "all" for the games parameter:
```bash
savegamesync --backup --cloud --games $Game1 $Game2
```
Copies the savestates from the game directory to the local backup location. If you want to copy all
 available games, use "all" for the games parameter.
```bash
savegamesync --backup --local --games $Game1 $Game2
```

Download the files from your Cloud to the correct location. If you want to download all
 available games, use "all" for the games parameter.
```bash
savegamesync --restore --cloud --games $Game1 $Game2
```
Copies the files from your local directory to the correct savestate location. If you want to download all
 available games, use "all" for the games parameter.
```bash
savegamesync --restore --local --games $Game1 $Game2
```
If you want to preserve the old backup. It is supported by local and cloud backup Use:
```bash
savegamesync --backup --local --preserve --games $Game1 $Game2
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
savegamesync --version
```
## Howto add games
If you miss a game, which is not listed here, just fork the project, add the missing game to the *games.xml* and send an submit request. If you don't know where the savestate of your game is located, check-out [PCGamingWiki](https://pcgamingwiki.com/wiki/Home). Linux savegame location is most probably listed there.

Here is an example of a xml snippet containing a game
```xml
    <game name="$GamenameForTheScript">
        <parent>$Relative Path to the parent directory of the game</parent>
        <gamedir>savegame directory relative to the parent directory from above.</gamedir>
    </game>
```

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
* FEZ
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
* consider to use yaml instead of xml

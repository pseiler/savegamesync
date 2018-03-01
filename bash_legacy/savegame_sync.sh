#!/bin/bash

## Error function
die(){
    echo "Error encountered"
    echo "Reason: $1"
    exit 1
}

## prevent from running as root
if [ $UID = 0 ]
then
    die "Do not run this script as root"
fi

### Functions ###
## check if every binary needed in this script is installed
if [ ! -x /usr/bin/curl ] && [ ! -x /bin/curl ]
then
    die "\"curl\" is not installed"
elif [ ! -x /usr/bin/tar ] && [ ! -x /bin/tar ]
then
    die "\"tar\" is not installed"
elif [ ! -x /usr/bin/gzip ] && [ ! -x /bin/gzip ]
then
    die "\"gzip\" is not installed"
fi

## check if $HOME Variable set
if [ -z $HOME ]
then
    die "\$HOME variable not set. script could have unforeseen behaviour"
fi

## usage/help function
usage(){
    echo ""
    echo "$0 provides savegame sync features for your owncloud/nextcloud instance"
    echo "Usage:"
    echo "$0 -u \"\$Game1, \$Game2\" uploads the files to your Cloud"
    echo "$0 -d \"\$Game1, \$Game2\" downloads the files from your Cloud"
    echo "                                     to the correct location" 
    echo ""
    echo "$0 -l                  lists all available games"
    echo "$0 -s                  Wizard for the configuration file"
    echo "$0 -h                  Shows this help message"
}

## functions for archiving and extract games

game_pack(){
    tar -C "${HOME}/${1}" -czf ${2}/${3}.tar.gz "${4}" &> /dev/null || die "Packing of \"${3}\" failed. Maybe no savestate available"
}
game_unpack(){
    if [ ! -d "${HOME}/${1}" ]
    then
        mkdir -p "${HOME}/${1}"
    fi
    tar -C "${HOME}/${1}"  -xzf ${2}/${3}.tar.gz
}

setup_configuration(){
    if [ ! -d ${CONFIG_DIR} ];
    then
        mkdir ${CONFIG_DIR}
        chmod 700 ${CONFIG_DIR}
    fi;
    echo "Creating configuration file in \"${CONFIG_DIR}/config.cfg\""
    ### domain Name
    echo "Enter your Cloud Domain Name:"
    read -r TMP_DOMAIN
    echo "CLOUD_DOMAIN=\"$TMP_DOMAIN\"" > ${CONFIG_DIR}/config.cfg
    ## webroot directory
    echo "Enter your Webservers directory where your Cloud is installed:"
    echo "(If you installed it directly into your webroot. leave it empty)"
    read -r TMP_URL_PATH
    if [ ! $TMP_URL_PATH = "" ]
    then
        echo "CLOUD_URL_PATH=\"$TMP_URL_PATH\"" >> ${CONFIG_DIR}/config.cfg
    fi
    # Username
    echo "Enter your Cloud username:"
    read -r TMP_USER
    echo "CLOUD_USER=\"$TMP_USER\"" >> ${CONFIG_DIR}/config.cfg
    # Password
    echo "Enter your Cloud Password for User \"$TMP_USER\":"
    echo "(The password is saved in cleartext. If you don't want"
    echo "use it, just press enter to leave it empty.)"
    read -s TMP_PASSWORD
    if [ ! ${TMP_PASSWORD} = "" ]
    then
        echo "CLOUD_PASSWORD=\"$TMP_PASSWORD\"" >> ${CONFIG_DIR}/config.cfg
    fi
    # savegame sync directory
    echo "Enter your Cloud sync directory:"
    read -r TMP_SYNC_DIR
    echo "CLOUD_SYNC_DIR=\"$TMP_SYNC_DIR\"" >> ${CONFIG_DIR}/config.cfg
    chmod 600 ${CONFIG_DIR}/config.cfg
}

########################################
########################################

AVAIL_GAMES=(AmnesiaADarkDescent Celeste Deponia1 Deponia2 Deponia3 Guacamelee Hacknet Hedgewars HollowKnight HunieCamStudio HuniePop OlliOlli OlliOlli2 Quake3 ShovelKnight Skullgirls SuperHexagon SuperMeatBoy TheEndIsNigh Teeworlds)

# Set upload and download to false
UPLOAD="no"
DOWNLOAD="no"

# Set configuration dir
CONFIG_DIR=${HOME}/.savegame_sync;

# declare parameters for getopts
while getopts ":udg:hls" option; do
    case "${option}" in
        u)
            UPLOAD="yes"
            ;;
        d)
            DOWNLOAD="yes"
            ;;
        g)
            GAMES_LIST=${OPTARG}
            ;;
        l)
            echo "Available Games:"
            echo "----------------"
            for l in ${AVAIL_GAMES[@]}
            do
                echo ${l}
            done
            exit 0
            ;;
        h)
            usage
            exit 0
            ;;
        s)
            echo "Be carefull. The configuration file will be overwritten. Cancel at first step to prevent this."
            echo ""
            setup_configuration
            echo ""
            echo "Successfully written your configuration file. Now rerun the script with other parameters."
            exit 0
            ;;
        *)
            echo "No valid parameter provided"
            usage
            exit 1
            ;;
    esac
done

### exception handling and build some variable pathes

# Configuration directory reading. Check it if its present
if [ -f ${CONFIG_DIR}/config.cfg ];
then
    source ${CONFIG_DIR}/config.cfg;
fi;

# Building URL from Domain name and url path
URL="https://${CLOUD_DOMAIN}/${CLOUD_URL_PATH}";

# Check if domain parameter is present
if [ -z $CLOUD_DOMAIN ];
then
    echo "No Nextcloud Domain entered";
    exit 1;
fi
# Check if user and password provided
if [ -z $CLOUD_USER ]
then
    die "No User provided"
fi
if [ -z $CLOUD_SYNC_DIR ]
then
    CLOUD_SYNC_DIR=savegames
    echo "Using standard sync directory \"${CLOUD_SYNC_DIR}\"."
fi

WEBDAV="$URL/remote.php/dav/files/${CLOUD_USER}"

# Check if any parameter was given
if [ $# -lt 1 ];
then
    echo "no parameter given. Please check your command line arguments";
    usage;
    exit 1;
fi

# Check if Password is set. If not read it from stdin
while [ -z $CLOUD_PASSWORD ];
do
    echo ""
    echo "No Password provided in configuration file."
    echo "Enter your password for user \"${CLOUD_USER}\":"
    read -rs CLOUD_PASSWORD
done

# Convert string with comma and space into array
IFS=', ' read -r -a GAMES_PARSED <<< "$GAMES_LIST"

# check if all games are available
# https://stackoverflow.com/questions/2312762/compare-difference-of-two-arrays-in-bash#28161520
for i in ${GAMES_PARSED[@]};
do
    skip=
    for j in ${AVAIL_GAMES[@]};
    do
        [[ $i == $j ]] && { skip=1; break; }
    done
    if ! [[ -n $skip ]]
    then
        die "Game \"${i}\" not found in supported Game list. Use \"$0 -l\"."
    fi
done

# check if both or no upload and download parameter is set
if [ $UPLOAD = "yes" ] && [ $DOWNLOAD = "yes" ]
then
    echo "Cannot download and upload at the same time. Please use only one of the parameters"
    usage
    exit 1
elif [ $UPLOAD = "no" ] && [ $DOWNLOAD = "no" ]
then
    echo "No \$Game parameter was used"
    usage
    exit 1
fi


for k in ${GAMES_PARSED[@]};
do
    case $k in
        Celeste|Hacknet|Skullgirls|SuperHexagon|SuperMeatBoy)
            MY_PARENT_DIR=".local/share"
            MY_DIR=${k}
            ;;
        AmnesiaADarkDescent)
            MY_PARENT_DIR=".local/share"
            MY_DIR=Amnesia
            ;;
        Deponia1)
            MY_PARENT_DIR=".local/share/Daedalic Entertainment"
            MY_DIR=Deponia
            ;;
        Deponia2)
            game_pack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k} "Deponia 2"
            ;;
        Deponia3)
            game_pack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k} "Deponia 3"
            ;;
        Guacamelee)
            game_pack "/.local/share/Drinkbox Studios" ${PACK_DIR} ${k} ${k}
            ;;
        Hedgewars)
            game_pack "" ${PACK_DIR} ${k} ".hedgewars"
            ;;
        HollowKnight)
            game_pack "/.config/unity3d/Team Cherry" ${PACK_DIR} ${k} "Hollow Knight"
            ;;
        HuniePop)
            game_pack "/.config/unity3d/HuniePot" ${PACK_DIR} ${k} ${k}
            ;;
        HunieCamStudio)
            game_pack "/.config/unity3d/HuniePot" ${PACK_DIR} ${k} "HunieCam Studio"
            ;;
        OlliOlli)
            game_pack "" ${PACK_DIR} ${k} ".olliolli"
            ;;
        OlliOlli2)
            game_pack "" ${PACK_DIR} ${k} ".olliolli2"
            ;;
        Quake3)
            game_pack "" ${PACK_DIR} ${k} ".q3a"
            ;;
        ShovelKnight)
            game_pack "/.local/share/Yacht Club Games" ${PACK_DIR} ${k} "Shovel Knight"
            ;;
        StardewValley)
            game_pack "/.config/" ${PACK_DIR} ${k} ${k}
            ;;
        TheEndIsNigh)
            game_pack "/.local/share/" ${PACK_DIR} ${k} "The End is Nigh"
            ;;
        Teeworlds)
            game_pack "" ${PACK_DIR} ${k} ".teeworlds"
            ;;
    esac
done


# do the actual upload
if [ $UPLOAD = "yes" ] && [ $DOWNLOAD = "no" ]
then
    echo "Creating remote Cloud directory \"$CLOUD_SYNC_DIR\" if not present..."
    # create the webdav sync directory
    curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -X MKCOL $WEBDAV/$CLOUD_SYNC_DIR &> /dev/null || die "Could not create or check directory. Maybe Internet connection errors"

    for k in ${GAMES_PARSED[@]};
    do
        PACK_DIR=$(mktemp -d /tmp/${k}.XXXXX)
        case $k in
            Celeste|Hacknet|Skullgirls|SuperHexagon|SuperMeatBoy)
#                game_pack "/.local/share/" ${PACK_DIR} ${k} ${k}
                MY_PARENT_DIR=".local/share"
                MY_DIR=${k}
                ;;
            AmnesiaADarkDescent)
#                game_pack "/.frictionalgames" ${PACK_DIR} ${k} Amnesia
                MY_PARENT_DIR=".local/share"
                MY_DIR=Amnesia
                ;;
            Deponia1)
#                game_pack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k} "Deponia"
                MY_PARENT_DIR=".local/share/Daedalic Entertainment"
                MY_DIR=Deponia
                ;;
            Deponia2)
                game_pack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k} "Deponia 2"
                ;;
            Deponia3)
                game_pack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k} "Deponia 3"
                ;;
            Guacamelee)
                game_pack "/.local/share/Drinkbox Studios" ${PACK_DIR} ${k} ${k}
                ;;
            Hedgewars)
                game_pack "" ${PACK_DIR} ${k} ".hedgewars"
                ;;
            HollowKnight)
                game_pack "/.config/unity3d/Team Cherry" ${PACK_DIR} ${k} "Hollow Knight"
                ;;
            HuniePop)
                game_pack "/.config/unity3d/HuniePot" ${PACK_DIR} ${k} ${k}
                ;;
            HunieCamStudio)
                game_pack "/.config/unity3d/HuniePot" ${PACK_DIR} ${k} "HunieCam Studio"
                ;;
            OlliOlli)
                game_pack "" ${PACK_DIR} ${k} ".olliolli"
                ;;
            OlliOlli2)
                game_pack "" ${PACK_DIR} ${k} ".olliolli2"
                ;;
            Quake3)
                game_pack "" ${PACK_DIR} ${k} ".q3a"
                ;;
            ShovelKnight)
                game_pack "/.local/share/Yacht Club Games" ${PACK_DIR} ${k} "Shovel Knight"
                ;;
            StardewValley)
                game_pack "/.config/" ${PACK_DIR} ${k} ${k}
                ;;
            TheEndIsNigh)
                game_pack "/.local/share/" ${PACK_DIR} ${k} "The End is Nigh"
                ;;
            Teeworlds)
                game_pack "" ${PACK_DIR} ${k} ".teeworlds"
                ;;
        esac
        game_pack $MY_PARENT_DIR ${PACK_DIR} ${k} ${MY_DIR}
        echo "Creating remote savegame directory \"$CLOUD_SYNC_DIR/${k}\"..."
        curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -X MKCOL $WEBDAV/$CLOUD_SYNC_DIR/${k} &> /dev/null || die
        echo "Uploading \"$k\" savegame..."
        curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -T ${PACK_DIR}/${k}.tar.gz $WEBDAV/$CLOUD_SYNC_DIR/${k}/${k}.tar.gz || die "Upload of Game \"${k}\" failed"
        rm -r $PACK_DIR
    done
elif [ $UPLOAD = "no" ] && [ $DOWNLOAD = "yes" ]
then
    for k in ${GAMES_PARSED[@]};
    do
        PACK_DIR=$(mktemp -d /tmp/${k}.XXXXX)
        echo "Downloading savestate for \"${k}\"..."
        curl --fail -u ${CLOUD_USER}:${CLOUD_PASSWORD} $WEBDAV/$CLOUD_SYNC_DIR/${k}/${k}.tar.gz 1> $PACK_DIR/${k}.tar.gz 2> /dev/null || die "No Savestate of \"${k}\" found."
        echo "Unpacking savestate for \"${k}\"..."
        case $k in
            Celeste|Hacknet|Skullgirls|SuperHexagon|SuperMeatBoy|TheEndIsNigh)
                game_unpack "/.local/share/" ${PACK_DIR} ${k}
                ;;
            AmnesiaADarkDescent)
                game_pack "/.frictionalgames" ${PACK_DIR} ${k}
                ;;
            Deponia1|Deponia2|Deponia3)
                game_unpack "/.local/share/Daedalic Entertainment" ${PACK_DIR} ${k}
                ;;
            HollowKnight)
                game_unpack "/.config/unity3d/Team Cherry" ${PACK_DIR} ${k}
                ;;
            HuniePop|HunieCamStudio)
                game_unpack "/.config/unity3d/HuniPot" ${PACK_DIR} ${k}
                ;;
            Hedgewars|OlliOlli|OlliOlli2|Quake3|Teeworlds)
                game_unpack "" ${PACK_DIR} ${k}
                ;;
            ShovelKnight)
                game_unpack "/.local/share/Yacht Club Games" ${PACK_DIR} ${k}
                ;;
            StardewValley)
                game_unpack "/.config/" ${PACK_DIR} ${k}
                ;;
        esac
        rm -r $PACK_DIR
    done
fi
exit 0

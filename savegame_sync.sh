#!/bin/bash

## Error function
die(){
    echo "Error encountered"
    echo "Reason: $1"
    exit 1
}

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


#usage/help function
usage(){
    echo ""
    echo "$0 provides savegame sync features for your owncloud/nextcloud instance"
    echo "Usage:"
    echo "$0 -u \"\$Game1, \$Game2\" uploads the files to your Cloud"
    echo "$0 -d \"\$Game1, \$Game2\" downloads the files from your Cloud"
    echo "                                     to the correct location" 
    echo ""
    echo "$0 -l                  lists all available games"
    echo "$0 -h                  Shows this help message"
}

AVAIL_GAMES=(Celeste Hollow_Knight Hacknet Deponia1 Deponia2 Deponia3 Skullgirls SuperHexagon)

#### Game specific commandos
# local_share (Skullgirls, Hacknet, Celeste, SuperHexagon)
localshare_pack(){
    tar -C ${HOME}/.local/share/ -czf ${1}/${2}.tar.gz ${2} &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
localshare_unpack(){
    if [ ! -d ${HOME}/.local/share/ ]
    then
        mkdir -p ${HOME}/.local/share/
    fi
    tar -C ${HOME}/.local/share/  -xzf ${1}/${2}.tar.gz
}
# Deponia series
deponia_pack(){
    tar -C "${HOME}/.local/share/Daedalic Entertainment" -czf ${1}/${2}.tar.gz "${3}" &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
deponia_unpack(){
    if [ ! -d "${HOME}/.local/share/Daedalic Entertainment" ]
    then
        mkdir -p "${HOME}/.local/share/Daedalic Entertainment"
    fi
    tar -C "${HOME}/.local/share/Daedalic Entertainment"  -xzf ${1}/${2}.tar.gz
}
# Hollow Knight
hollow_knight_pack(){
    tar -C "${HOME}/.config/unity3d/Team Cherry/" -czf ${1}/${2}.tar.gz Hollow\ Knight &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
hollow_knight_unpack(){
    if [ ! -d "${HOME}/.config/unity3d/Team Cherry" ]
    then
        mkdir -p "${HOME}/.config/unity3d/Team Cherry"
    fi
    tar -C "${HOME}/.config/unity3d/Team Cherry/"  -xzf ${1}/${2}.tar.gz
}
# config (StardewValley)
config_pack(){
    tar -C "${HOME}/.config/" -czf ${1}/${2}.tar.gz ${2} &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
config_knight_unpack(){
    if [ ! -d "${HOME}/.config" ]
    then
        mkdir -p "${HOME}/.config"
    fi
    tar -C "${HOME}/.config/unity3d/"  -xzf ${1}/${2}.tar.gz
}

### Configuration directory reading. Check it if its present
CONFIG_DIR=${HOME}/.savegame_sync;
if [ -f ${CONFIG_DIR}/config.cfg ];
then
    chmod 700 ${CONFIG_DIR}
    chmod 600 ${CONFIG_DIR}/config.cfg
    source ${CONFIG_DIR}/config.cfg;
fi;

## Building URL from Domain name and url path
URL="https://${CLOUD_DOMAIN}/${CLOUD_URL_PATH}";

#Check if domain parameter is present
if [ -z $CLOUD_DOMAIN ];
then
    echo "No Nextcloud Domain entered";
    exit 1;
fi
#check if user and password provided
if [ -z $CLOUD_USER ]
then
    die "No User provided"
fi
while [ -z $CLOUD_PASSWORD ];
do
    echo ""
    echo "No Password provided"
    echo "Enter your password for user \"${CLOUD_USER}\":"
    read -rs CLOUD_PASSWORD
done

if [ -z $CLOUD_SYNC_DIR ]
then
    CLOUD_SYNC_DIR=savegames
    echo "Using standard sync directory \"${CLOUD_SYNC_DIR}\"."
fi

WEBDAV="$URL/remote.php/dav/files/${CLOUD_USER}"

# Set upload and download to false
UPLOAD="no"
DOWNLOAD="no"

# declare parameters for getopts
while getopts ":u:d:hl" option; do
    case "${option}" in
        u)
            u=${OPTARG}
            UPLOAD="yes"
            ;;
        d)
            d=${OPTARG}
            DOWNLOAD="yes"
            ;;
        l)
            echo "Available Games:"
            echo ""
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
        *)
            echo "No valid parameter provided"
            usage
            exit 1
            ;;
    esac
done

# Check if any parameter was given
if [ $# -lt 1 ];
then
    echo "no parameter given. Please check your command line arguments";
    usage;
    exit 1;
fi

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
# do the actual upload
elif [ $UPLOAD = "yes" ] && [ $DOWNLOAD = "no" ]
then
    curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -X MKCOL $WEBDAV/$CLOUD_SYNC_DIR &> /dev/null || die "Could not create or check directory. Maybe Internet connection errors"
    IFS=', ' read -r -a GAMES_LIST <<< "$u"
    # check if all games are available
    # https://stackoverflow.com/questions/2312762/compare-difference-of-two-arrays-in-bash#28161520
    for i in ${GAMES_LIST[@]};
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
    for k in ${GAMES_LIST[@]};
    do
        PACK_DIR=$(mktemp -d /tmp/${k}.XXXXX)
        case $k in
            Celeste|Hacknet|Skullgirls|SuperHexagon)
                localshare_pack ${PACK_DIR} ${k}
                ;;
            Hollow_Knight)
                hollow_knight_pack ${PACK_DIR} ${k}
                ;;
            StardewValley)
                config_pack ${PACK_DIR} ${k}
                ;;
            Deponia1)
                deponia_pack ${PACK_DIR} ${k} 'Deponia'
                ;;
            Deponia2)
                deponia_pack ${PACK_DIR} ${k} 'Deponia 2'
                ;;
            Deponia3)
                deponia_pack ${PACK_DIR} ${k} 'Deponia 3'
                ;;
        esac
        curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -X MKCOL $WEBDAV/$CLOUD_SYNC_DIR/${k} &> /dev/null || die
        echo "Uploading \"$k\" savegame"
        curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -T ${PACK_DIR}/${k}.tar.gz $WEBDAV/$CLOUD_SYNC_DIR/${k}/${k}.tar.gz || die "Upload of Game \"${k}\" failed"
        rm -r $PACK_DIR
    done
elif [ $UPLOAD = "no" ] && [ $DOWNLOAD = "yes" ]
then
    IFS=', ' read -r -a GAMES_LIST <<< "$d"
    # check if all games are available
    # https://stackoverflow.com/questions/2312762/compare-difference-of-two-arrays-in-bash#28161520
    for i in ${GAMES_LIST[@]};
    do
        skip=
        for j in ${AVAIL_GAMES[@]};
        do
            [[ $i == $j ]] && { skip=1; break; }
        done
        if ! [[ -n $skip ]]
        then
            echo "Game \"$i\" not found"
            exit 1
        fi
    done
    for k in ${GAMES_LIST[@]};
    do
        PACK_DIR=$(mktemp -d /tmp/${k}.XXXXX)
        echo "Downloading savestate for \"${k}\""
        curl --fail -u ${CLOUD_USER}:${CLOUD_PASSWORD} $WEBDAV/$CLOUD_SYNC_DIR/${k}/${k}.tar.gz 1> $PACK_DIR/${k}.tar.gz 2> /dev/null || die "No Savestate of \"${k}\" found."
        echo "Unpacking savestate for \"${k}\""
        case $k in
            Celeste|Hacknet|Skullgirls|SuperHexagon)
                localshare_unpack ${PACK_DIR} ${k}
                ;;
            Hollow_Knight)
                hollow_knight_unpack ${PACK_DIR} ${k}
                ;;
            StardewValley)
                config_unpack ${PACK_DIR} ${k}
                ;;
            Deponia1)
                deponia_unpack ${PACK_DIR} ${k}
                ;;
            Deponia2)
                deponia_unpack ${PACK_DIR} ${k}
                ;;
            Deponia3)
                deponia_unpack ${PACK_DIR} ${k}
                ;;
        esac
        rm -r $PACK_DIR
    done
fi

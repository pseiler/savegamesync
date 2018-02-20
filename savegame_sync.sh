#!/bin/bash

#usage/help function
usage(){
    echo ""
    echo "$0 provides savegame sync features for your owncloud/nextcloud instance"
    echo "Usage:"
    echo "$0 -u \"\$Game1, \$Game2\" uploads the files to your Cloud"
    echo "$0 -d \"\$Game1, \$Game2\" downloads the files from your Cloud to the correct location" 
    echo "$0 -l                  lists all available games" 
}

die(){
    echo "Error encountered"
    exit 1
}

AVAIL_GAMES=(Celeste Hollow_Knight)

# Celeste packing function
celeste_pack(){
    tar -C ${HOME}/.local/share/ -czf ${1}/Celeste.tar.gz Celeste
}

# Celeste unpacking function


# Set upload and download to false
UPLOAD="no"
DOWNLOAD="no"

# declare parameters for getopts
while getopts ":u:d:h" option; do
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
            l=${OPTARG}
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
### Configuration directory reading. Check it if its present
CONFIG_DIR=/etc/savegame_sync;
if [ -f ${CONFIG_DIR}/config.cfg ];
then
    source ${CONFIG_DIR}/config.cfg;
fi;

## Building URL from Domain name and url path
URL="https://${MY_DOMAIN}/${MY_URL_PATH}";

#Check if domain parameter is present
if [ -z $MY_DOMAIN ];
then
    echo "No Nextcloud Domain entered";
    exit 1;
fi
#check if user and password provided
if [ -z $MY_USER ] || [ -z $MY_PASSWORD ];
then
    echo "No User and/or Password provided";
    exit 1;
fi

if [ -z $MY_SYNC_DIR ]
then
    MY_SYNC_DIR=savegames
    echo "Using standard sync directory \"${MY_SYNC_DIR}\"."
fi

WEBDAV="$URL/remote.php/dav/files/${MY_USER}"



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
    curl -u ${MY_USER}:${MY_PASSWORD} -X MKCOL $WEBDAV/$MY_SYNC_DIR &> /dev/null || die
    IFS=', ' read -r -a GAMES_LIST <<< "$u"
    echo "Upload Game(s) \"${GAMES_LIST[@]}\""
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
        case $k in
            Celeste)
                celeste_pack $PACK_DIR
                ;;
        esac
        curl -u ${MY_USER}:${MY_PASSWORD} -X MKCOL $WEBDAV/$MY_SYNC_DIR/${k} &> /dev/null || die
        echo "Uploading \"$k\" savegame"
        curl -u ${MY_USER}:${MY_PASSWORD} -T ${PACK_DIR}/${k}.tar.gz $WEBDAV/$MY_SYNC_DIR/${k}/${k}.tar.gz || die
        rm -r $PACK_DIR
    done
fi

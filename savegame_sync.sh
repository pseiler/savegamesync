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
    echo "$0 -s                  Wizard for the configuration file"
    echo "$0 -h                  Shows this help message"
}

AVAIL_GAMES=(Celeste Deponia1 Deponia2 Deponia3 Guacamelee Hacknet HollowKnight HunieCamStudio HuniePop Skullgirls SuperHexagon SuperMeatBoy)

#########################################################
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
###
# localshare with developer subdirectory
localsharedev_pack(){
    tar -C "${HOME}/.local/share/${3}" -czf ${1}/${2}.tar.gz "${4}" &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
localsharedev_unpack(){
    if [ ! -d "${HOME}/.local/share/${3}" ]
    then
        mkdir -p "${HOME}/.local/share/${3}"
    fi
    tar -C "${HOME}/.local/share/${3}"  -xzf ${1}/${2}.tar.gz
}
###
# config (StardewValley)
config_pack(){
    tar -C "${HOME}/.config/" -czf ${1}/${2}.tar.gz ${2} &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
config_unpack(){
    if [ ! -d "${HOME}/.config" ]
    then
        mkdir -p "${HOME}/.config"
    fi
    tar -C "${HOME}/.config"  -xzf ${1}/${2}.tar.gz
}
###
# unity (HollowKnight HunieCamStudio HuniePop)
unity_pack(){
    tar -C "${HOME}/.config/unity3d/${3}/" -czf ${1}/${2}.tar.gz "${4}" &> /dev/null || die "Packing of \"${2}\" failed. Maybe no savestate available"
}
unity_unpack(){
    if [ ! -d "${HOME}/.config/unity3d/${3}" ]
    then
        mkdir -p "${HOME}/.config/unity3d/${3}"
    fi
    tar -C "${HOME}/.config/unity3d/${3}/"  -xzf ${1}/${2}.tar.gz
}

##########################################################

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
    echo "If you installed it directly into your webroot. leave it empty."
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

# Set upload and download to false
UPLOAD="no"
DOWNLOAD="no"

# Set configuration dir
CONFIG_DIR=${HOME}/.savegame_sync;

# declare parameters for getopts
while getopts ":u:d:hls" option; do
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

### Configuration directory reading. Check it if its present
if [ -f ${CONFIG_DIR}/config.cfg ];
then
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

while [ -z $CLOUD_PASSWORD ];
do
    echo ""
    echo "No Password provided in configuration file."
    echo "Enter your password for user \"${CLOUD_USER}\":"
    read -rs CLOUD_PASSWORD
done


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
    echo "Creating remote Cloud directory \"$CLOUD_SYNC_DIR\" if not present..."
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
            Celeste|Hacknet|Skullgirls|SuperHexagon|SuperMeatBoy)
                localshare_pack ${PACK_DIR} ${k}
                ;;
            Deponia1)
                localsharedev_pack ${PACK_DIR} ${k} "Daedalic Entertainment" "Deponia"
                ;;
            Deponia2)
                localsharedev_pack ${PACK_DIR} ${k} "Daedalic Entertainment" "Deponia 2"
                ;;
            Deponia3)
                localsharedev_pack ${PACK_DIR} ${k} "Daedalic Entertainment" "Deponia 3"
                ;;
            Guacamelee)
                localsharedev_pack ${PACK_DIR} ${k} "Drinkbox Studios" "${k}"
                ;;
            HollowKnight)
                unity_pack ${PACK_DIR} ${k} "Team Cherry" "Hollow Knight"
                ;;
            HuniePop)
                unity_pack ${PACK_DIR} ${k} "HuniePot" "HuniePop"
                ;;
            HunieCamStudio)
                unity_pack ${PACK_DIR} ${k} "HuniePot" "HunieCam Studio"
                ;;
            StardewValley)
                config_pack ${PACK_DIR} ${k}
                ;;
        esac
        echo "Creating remote savegame directory \"$CLOUD_SYNC_DIR/${k}\"..."
        curl -u ${CLOUD_USER}:${CLOUD_PASSWORD} -X MKCOL $WEBDAV/$CLOUD_SYNC_DIR/${k} &> /dev/null || die
        echo "Uploading \"$k\" savegame..."
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
        echo "Downloading savestate for \"${k}\"..."
        curl --fail -u ${CLOUD_USER}:${CLOUD_PASSWORD} $WEBDAV/$CLOUD_SYNC_DIR/${k}/${k}.tar.gz 1> $PACK_DIR/${k}.tar.gz 2> /dev/null || die "No Savestate of \"${k}\" found."
        echo "Unpacking savestate for \"${k}\"..."
        case $k in
            Celeste|Hacknet|Skullgirls|SuperHexagon|SuperMeatBoy)
                localshare_unpack ${PACK_DIR} ${k}
                ;;
            Deponia1)
                localsharedev_unpack ${PACK_DIR} ${k} "Daedalic Entertainment"
                ;;
            Deponia2)
                localsharedev_unpack ${PACK_DIR} ${k} "Daedalic Entertainment"
                ;;
            Deponia3)
                localsharedev_unpack ${PACK_DIR} ${k} "Daedalic Entertainment"
                ;;
            HollowKnight)
                unity_unpack ${PACK_DIR} ${k} "Team Cherry"
                ;;
            HuniePop|HunieCamStudio)
                unity_unpack ${PACK_DIR} ${k} "HuniePot"
                ;;
            StardewValley)
                config_unpack ${PACK_DIR} ${k}
                ;;
        esac
        rm -r $PACK_DIR
    done
fi
exit 0

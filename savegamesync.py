#!/usr/bin/python
import sys
# output piping is not working without utf-8 encoding
reload(sys)
sys.setdefaultencoding('utf-8')

import argparse
import os
import xml.etree.ElementTree
import ConfigParser
import tarfile
from tempfile import mkdtemp
from shutil import rmtree
from shutil import copyfile
import pycurl
import getpass
import base64
try:
        from io import BytesIO
except ImportError:
        from StringIO import StringIO as BytesIO

# define base variables
script_name = os.path.basename(__file__)
savegame = "savegame"
version = "0.0.1"

# check if script is running as root
if os.getuid() == 0:
    print "%s is not designed to run as root. Please" % script_name
    print "use a normal user account."
    sys.exit(2)

##### functions
# test if file or directory is available on webdav/cloud
def curl_test(url, user, password):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.CUSTOMREQUEST, "PROPFIND")
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    http_return = c.getinfo(c.RESPONSE_CODE)
    c.close()
    return http_return

# create a directory on webdav/cloud
def curl_mkdir(url, user, password):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.CUSTOMREQUEST, "MKCOL")
    c.perform()
    c.close()

# move a file or directory to a new destination on webdav/cloud
def curl_mv(url, new_url, user, password):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.CUSTOMREQUEST, "MOVE")
    c.setopt(pycurl.HTTPHEADER, ["Destination:" + new_url])
    c.perform()
    c.close()

# upload a file to webdav/cloud
def curl_upload(url, local_file, user, password):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.UPLOAD, 1)
    c.setopt(pycurl.READFUNCTION, open(local_file, 'rb').read)
    c.perform()
    c.close()

# download a file from webdav/cloud
def curl_download(url, local_file, user, password):
    with open(local_file, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, url)
#        c.setopt(c.VERBOSE, True)
        c.setopt(pycurl.USERPWD, user + ':' + password)
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()

# setup wizard for the configuration file
def setup_config(path_to_config):
    config_domain = raw_input("Domain address for your Cloud [your.cloud.domain] (can be empty): ")
    config_user = raw_input("User for your Cloud (can be empty): ")
    pw_check = False
    while not pw_check:
        config_password = getpass.getpass("Password for your Cloud (can be empty): ")
        if not config_password:
            pw_check = True
        else:
            config_password_check = getpass.getpass("Repeat password: ")
            if (config_password == config_password_check):
                pw_check = True
            else:
                print "Passwords didn't match. Try again"
    config_url_path = raw_input("Webserver Document Root [/owncloud] (can be empty): ")
    config_remote_dir = raw_input("Sync directory for your Cloud [savegames] (can be empty): ")
    config_local_dir = raw_input("local directory [/home/$USER/savegames] (can be empty): ")
    config_password = base64.b64encode(config_password)
    config_setup = ConfigParser.ConfigParser()
    with open(path_to_config, 'wb') as f:
        config_setup.add_section('main')
        if config_domain:
            config_setup.set('main', 'domain', config_domain)
        if config_user:
            config_setup.set('main', 'user', config_user)
        if config_password:
            config_setup.set('main', 'password', config_password)
        if config_url_path:
            config_setup.set('main', 'url_path', config_url_path)
        if config_remote_dir:
            config_setup.set('main', 'remote_dir', config_remote_dir)
        if config_local_dir:
            config_setup.set('main', 'local_dir', config_local_dir)
        config_setup.write(f)
    print "Wrote configuration file \"%s\"." % path_to_config

# check if configuration has option
def config_has_option(object, section, option, path):
    if not object.has_option(section, option):
        print "No attribute \"%s\" in \"%s\"" % (option, path)
        sys.exit(2)

# Setting booleans to false (used to control the behaviour of the script
download = False
upload = False
games_enabled = False

# setting the home variable
my_home = os.environ['HOME']
config_path = "%s/.savegamesync.conf" % my_home

# check if the games.xml is in any of the following pathes
## read bash environment variable
xdg_tmp = os.environ['XDG_DATA_DIRS']
# convert it to a list
xdg_data_dir = xdg_tmp.split(':')

# add for every found list entry a subdirectory with the name of the script
for i in xrange(len(xdg_data_dir)):
    xdg_data_dir[i] = xdg_data_dir[i] + '/' + script_name

# remove unneeded variable from above
del xdg_tmp

# add the scripts directory to directory searching for the script
xdg_data_dir.append(os.path.dirname(os.path.abspath(__file__)))

# set the directory for games.xml. ordering: /usr/local/share -> /usr/share -> script directory
for i in xdg_data_dir:
    if os.path.exists(i + "/games.xml"):
        games_config = i + "/games.xml"

try: games_config
except NameError:
    print "No valid \"games.xml\" found."
    print "Put it in one of the following directories:"
    print ""
    for i in xdg_data_dir:
        print i + '/'
    sys.exit(2)

# read the xml file
xml_parsed = xml.etree.ElementTree.parse(games_config).getroot()

# create game list from xml
avail_games = []
for game in xml_parsed.findall('game'):
    avail_games.append(game.get('name'))

## script parameter handling
parser = argparse.ArgumentParser(prog=script_name, usage='%(prog)s [options]')
parser.add_argument('--backup', '-b', action='store_true', help="backup the games")
parser.add_argument('--restore', '-r', action='store_true', help="download the games")
parser.add_argument('--games', '-g', nargs='+', help="specifies the games")
parser.add_argument('--setup', '-s', action='store_true', help="Wizard to generate configuration file")
parser.add_argument('--local', '-d', action='store_true', help="backup/restore files to local directory")
parser.add_argument('--cloud', '-c', action='store_true', help="backup/restore files to Cloud")
parser.add_argument('--preserve', '-p', action='store_true', help="Don't overwrite the old %s" % savegame)
parser.add_argument('--list', '-l', action='store_true', help="List all available games")
parser.add_argument('--version', action='version', version='%(prog)s v0.0.2')
args = parser.parse_args()

if (args.backup or args.restore or args.local or args.list or args.games or args.cloud or args.local) and args.setup:
    print "Error: Cannot use --setup or -s together with other options."
    parser.print_help()
    sys.exit(2)
elif args.setup:
   setup_config(config_path)
   sys.exit(0)

if (args.backup or args.restore or args.local or args.setup or args.games or args.cloud or args.local) and args.list:
    print "Error: Cannot use --list or -l together with other options."
    parser.print_help()
    sys.exit(2)
elif args.list:
    print "Available Games"
    print "---------------"
    print
    for games in sorted(avail_games):
        print games
    sys.exit(0)

# check if "all" parameter for games is set. If not compare every listed game against supportet game list
if args.games:
    if args.games[0] == "all":
        games_array = avail_games
    else:
        games_array = args.games
        mismatch = []
        for element in games_array:
            if element not in avail_games:
                mismatch.append(element)
        if mismatch:
            print "Following games not found:"
            for i in mismatch:
                print i
            sys.exit(2)
# check if any games defined
try:
    games_array
except NameError:
    print "No Games defined. Please use -g [--games] and a list of games."
    sys.exit(2)

# check if configuration file exists on filesystem
if os.path.exists(config_path):
#        print "Configuration file doesn't exist"
#        print "Use \"%s --setup\" to create one." % script_name
#        sys.exit(2)
    ## read configuration file
    myconfig = ConfigParser.ConfigParser()
    myconfig.read(config_path)
    # check if main section is present
    if not myconfig.has_section('main'):
        print "No section [\"main\"] in \"%s\"" % config_path
        sys.exit(2)

    #only do this when cloud syncing is enabled
    if args.cloud:
        # check if config option is set. If not print an error and exit
        config_has_option(myconfig, 'main', 'domain', config_path)
        config_has_option(myconfig, 'main', 'user', config_path)
        # set domain and user from config parameters
        my_domain = myconfig.get('main', 'domain')
        my_user = myconfig.get('main', 'user')
        # check optional parameters and set default if not present
        if myconfig.has_option('main', 'url_path'):
            my_url_path = myconfig.get('main', 'url_path')
        else:
            my_url_path = ""
        my_webdav = "https://%s/%s/remote.php/dav/files/%s" % (my_domain, my_url_path, my_user)

        if myconfig.has_option('main', 'remote_dir'):
            my_remote_dir = myconfig.get('main', 'remote_dir')
        else:
            my_remote_dir = "savegames"
        # check if password is set. If not, read it from stdin
        if myconfig.has_option('main', 'password'):
            my_password = base64.b64decode(myconfig.get('main', 'password'))
        else:
            # get password from stdin
            my_password = getpass.getpass("Password for your Cloud: ")
    # read local_dir configuration only when local dir syncing is enabled
    if args.local:
        if myconfig.has_option('main', 'local_dir'):
            my_local_dir = myconfig.get('main', 'local_dir')

# set the directory path if no configuration found to local sync your savegames
else:
    my_local_dir = my_home + "/savegames"


# upload/download checks. Test if both or none of the two options set
if not args.backup and not args.restore:
    print "No backup or restore arguments given. Please use at least -b or -r, --games\n"
    parser.print_help()
    sys.exit(2)
elif args.backup and args.restore:
    print "Both backup and restore argument given. Please only use one of them"
    parser.print_help()
    sys.exit(2)

# check if an actual process of task should be done. (check if local file and/or cloud tasks should be done). Exit if none of them is set
if not args.cloud and not args.local:
    print "Nothing to do. Use at least -c [--cloud] or -d [--local] parameter"
    print
    parser.print_help()
    sys.exit(2)

if args.cloud and args.backup:
    # check if sync directory exists. If not create it
    if ( curl_test(my_webdav + '/' + my_remote_dir, my_user, my_password) == 404 ):
        print "Creating the sync directory \"%s\"" % my_remote_dir
        add_dir = my_webdav
        for i in my_remote_dir.split('/'):
            add_dir = add_dir + '/' + i
            curl_mkdir(add_dir, my_user, my_password)

for element in games_array:
    # create temporary directory
    tmp_dir = mkdtemp(prefix="%s." % (element))
    if args.cloud:
        my_file_url = my_webdav + '/' + my_remote_dir + '/' + element + '/' + element + '.tar.gz'
    for i in xml_parsed.findall('game'):
        if element == i.get('name'):
            parent = i.find('parent').text
            gamedir = i.find('gamedir').text

    # check if parent directory is set. Some directories do not have a parent part. Such like OlliOlli
    if parent:
        fulldir = "%s/%s/%s" % (my_home, parent, gamedir)
    else:
        fulldir = "%s/%s" % (my_home, gamedir)
    # check if upload parameter is set
    if args.backup:
        # check if directory of game exists. Otherwhite print an error and exit
        if not os.path.exists(fulldir):
            print "Warning: Path \"%s\" doesn't exist." % fulldir
            print "Do you have a local %s of \"%s\"?" % (savegame, element)
            print
        else:
            # creating tar file
            print "Creating archive for \"%s\"..." % element
            tar = tarfile.open(tmp_dir + '/' + element + '.tar.gz', "w:gz")
            tar.add(fulldir, arcname=gamedir )
            tar.close()
            # doing stuff when cloud sync is enabled
            if args.cloud:
                # check if the remote directory of specific game exists. If not create it
                if ( curl_test(my_webdav + '/' + my_remote_dir + '/' + element, my_user, my_password) == 404 ):
                    print "Creating the remote game directory \"%s\"..." % element
                    curl_mkdir(my_webdav + '/' + my_remote_dir + '/' + element, my_user, my_password)
                # if preserve is enabled copy the old savefile to *_old
                if args.preserve:
                    # check if there is already a file on the server
                    if not ( curl_test(my_file_url, my_user, my_password) == 404):
                        print "Renaming old remote \"%s\" %s to %s_old.tar.gz..." % (element, savegame, element)
                        curl_mv(my_file_url, my_webdav + '/' + my_remote_dir + '/' + element + '/' + element + '_old.tar.gz', my_user, my_password)
                # Do the actual curl curl upload
                print "Uploading current \"%s\" %s to Cloud..." % (element, savegame)
                curl_upload(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)
            #doing stuff when local sync is enabled
            if args.local:
                # check if local backup directory already exists. If not create it
                if not os.path.exists(my_local_dir):
                    print "Creating local backup directory \"%s\"..." % (my_local_dir)
                    os.makedirs(my_local_dir, 0775)
                # check if local game backup directory already exists. If not create it
                if not os.path.exists(my_local_dir + '/' + element):
                    print "Creating backup game directory \"%s/%s\"..." % (my_local_dir, element)
                    os.makedirs(my_local_dir + '/' + element, 0775)
                # if preserve is enabled copy the old savefile to *_old
                if args.preserve:
                    # check if local savegame file exists
                    if os.path.exists(my_local_dir + '/' + element + '/' + '/' + element + '.tar.gz'):
                        print "Renaming old local \"%s\" %s to %s_old.tar.gz..." % (element, savegame, element)
                        copyfile(my_local_dir + '/' + element + '/' + element + '.tar.gz', my_local_dir + '/' + element + '/' + element + '_old.tar.gz')
                #copy the current game savestate to local backup directory
                print "Copying current \"%s\" %s to the local backup directory..." % (element, savegame)
                copyfile(tmp_dir + '/' + element + '.tar.gz', my_local_dir + '/' + element + '/' + element + '.tar.gz')
            print
## Doings when downloading
    # check if restore parameter is set
    elif args.restore:
        # stuff that only affect cloud sync
        if args.cloud:
        #check if backup of savestate is available remote
            if ( curl_test(my_webdav + '/' + my_remote_dir + '/' + element + '/' + element + '.tar.gz', my_user, my_password) == 404 ):
                print "Warning: Savestate \"%s\" not found on remote Server \"%s\"." % (element, my_domain)
                print "Cannot sync savestate from Cloud"
                print

            else:
                # download the file to temp dir
                print "Downloading the %s of \"%s\"..." % (savegame, element)
                curl_download(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)
        elif args.local:
            # check if local backup is available
            if not os.path.exists(my_local_dir + '/' + element + '/' + element + '.tar.gz'):
               print "Local backup of %s doesn't exist. Skip..." % element
            else:
                print "Copy local backup of \"%s\"" % element
                copyfile(my_local_dir + '/' + element + '/' + element + '.tar.gz', tmp_dir + '/' + element + '.tar.gz')
                # extract the tar file
        # if temporary file file exists, restore the backup
        if os.path.exists(tmp_dir + '/' + element + '.tar.gz'):
            tar = tarfile.open(tmp_dir + '/' + element + '.tar.gz', "r:gz")
            # check if parent variable is set. Change extract path if not set. Usefull for games like OlliOlli
            if parent:
                # check if parent directories of game exists. If not create everything
                if not os.path.exists(my_home + '/' + parent):
                    print "Creating parent directory \"%s\"..." % parent
                    os.makedirs(my_home + '/' + parent, 0775)

                print "Extracting %s of \"%s\"..." % (savegame, element)
                tar.extractall(path=my_home + '/' + parent)
            else:
                tar.extractall(path=my_home)
                print "Extracting %s of \"%s\"..." % (savegame, element)
            tar.close()
        print

    # removing temporary tar file in tmp directory
    rmtree(tmp_dir)

sys.exit(0)

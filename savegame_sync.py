#!/usr/bin/python
import getopt
import sys
import os
import xml.etree.ElementTree
import ConfigParser
import tarfile
from tempfile import mkdtemp
from shutil import rmtree
import pycurl
import getpass
try:
        from io import BytesIO
except ImportError:
        from StringIO import StringIO as BytesIO

script_name = os.path.basename(__file__)
savegame = "savestate"


##### functions
def usage():
    print "Usage:"
    print "%s -u [--upload] --games \"$Game1, $Game2\"   uploads the files to your Cloud" % script_name
    print ""
    print "%s -d [--download] --games \"$Game1, $Game2\" downloads the files from your Cloud" % script_name
    print "                                                          to the correct location" 
    print ""
    print "%s -l [--list]                              lists all available games" % script_name
    print ""
    print "%s -s [--setup]                             Wizard for the configuration file" % script_name
    print ""
    print "%s -h [--help]                              Shows this help message" % script_name
    print ""

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

def curl_mkdir(url, user, password):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.CUSTOMREQUEST, "MKCOL")
    c.perform()
    c.close()

def curl_upload(url, local_file, user, password):
    c = pycurl.Curl()
    c.setopt(c.URL, url)
#    c.setopt(c.VERBOSE, True)
    c.setopt(pycurl.USERPWD, user + ':' + password)
    c.setopt(pycurl.UPLOAD, 1)
    c.setopt(pycurl.READFUNCTION, open(local_file, 'rb').read)
    c.perform()
    c.close()

def curl_download(url, local_file, user, password):
    with open(local_file, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, url)
#        c.setopt(c.VERBOSE, True)
        c.setopt(pycurl.USERPWD, user + ':' + password)
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()

def setup_config(path_to_config):
    config_domain = raw_input("Domain address for your Cloud [your.cloud.domain]: ")
    config_user = raw_input("User for your Cloud: ")
    pw_check = 1
    while (pw_check == 1):
        config_password = getpass.getpass("Password for your Cloud: ")
        config_password_check = getpass.getpass("Repeat password: ")
        if (config_password == config_password_check):
            pw_check = 0
        else:
            print "Passwords didn't match. Try again"
    config_sync_dir = raw_input("Sync directory for your Cloud [savegames] (can be empty): ")
    config_url_path = raw_input("Webserver Document Root [/owncloud] (can be empty): ")
    config_setup = ConfigParser.ConfigParser()
    with open(path_to_config, 'wb') as f:
        config_setup.add_section('main')
        config_setup.set('main', 'domain', config_domain)
        config_setup.set('main', 'user', config_user)
        config_setup.set('main', 'password', config_password)
        if config_url_path:
            config_setup.set('main', 'url_path', config_url_path)
        if config_sync_dir:
            config_setup.set('main', 'sync_dir', config_sync_dir)
        config_setup.write(f)

def config_has_option(object, section, option, path):
    if not object.has_option(section, option):
        print "No attribute \"%s\" in \"%s\"" % (option, path)
        sys.exit(2)
download = False
upload = False
games_enabled = False

my_home = os.environ['HOME']
config_path = "%s/.savegame_sync.conf" % my_home
xml_parsed = xml.etree.ElementTree.parse('games.xml').getroot()

# create game list from xml
avail_games = []
for game in xml_parsed.findall('game'):
    avail_games.append(game.get('name'))

# define parameters
try:
    opts, args = getopt.getopt(sys.argv[1:], 'dushl', ['help', 'list', 'upload', 'download','games=', 'setup'])
except getopt.GetoptError:
    print "Wrong arguments given."
    usage()
    sys.exit(2)
 
for opt, arg in opts:
    if opt in ('-h', '--help'):
        print "%s provides %s sync features for your owncloud/nextcloud instance" % (script_name, savegame)
        usage()
        sys.exit(2)
    elif opt in ('-u', '--upload'):
        upload = True
    elif opt in ('-d', '--download'):
        download = True
    elif opt in ('-l', '--list'):
        print "Available Games"
        print "---------------"
        print
        for games in sorted(avail_games):
            print '* ' + games
        sys.exit(0)
    elif opt in ('--games'):
        games = arg
        games_enabled = True
    elif opt in ('-s', '--setup'):
        setup_config(config_path)
        sys.exit(0)
    else:
        print "No arguments given"
        usage()
        sys.exit(2)
try:
    games
except NameError:
    print "No games defined. Use --games \"$game1, $game2, $game3\" Parameter"
    print ""
    usage()
    sys.exit(1)
games_array = games.split(", ")
mismatch = []
for element in games_array:
    if element not in avail_games:
        mismatch.append(element) 
if mismatch:
    print "Following games not found:"
    for i in mismatch:
        print i
    sys.exit(2)


## read configuration file
myconfig = ConfigParser.ConfigParser()
myconfig.read(config_path)
# check if main section is present
if not myconfig.has_section('main'):
    print "No section [\"main\"] in \"%s\"" % config_path
    sys.exit(2)


# check if config option is set. If not print an error and exit
config_has_option(myconfig, 'main', 'domain', config_path)
config_has_option(myconfig, 'main', 'user', config_path)
config_has_option(myconfig, 'main', 'password', config_path)

# check optional parameters and set default if not present
if myconfig.has_option('main', 'url_path'):
    my_url_path = myconfig.get('main', 'url_path')
else:
    my_url_path = ""

if myconfig.has_option('main', 'sync_dir'):
    my_sync_dir = myconfig.get('main', 'sync_dir')
else:
    my_sync_dir = "savegames"
# set variables from config parameters
my_domain = myconfig.get('main', 'domain')
my_user = myconfig.get('main', 'user')
my_password = myconfig.get('main', 'password')

# build standard url from parameters
my_webdav = "https://%s/%s/remote.php/dav/files/%s" % (my_domain, my_url_path, my_user)


# upload/download checks. Test if both or none of the two options set
if not download and not upload:
    print "No upload or download arguments given. Please use at least -u or -d and --games\n"
    usage()       
    sys.exit(2)
elif download and upload:
    print "Both upload and download argument given. Please only use one of them"
    usage()
    sys.exit(2)

for element in games_array:
    my_file_url = my_webdav + '/' + my_sync_dir + '/' + element + '/' + element + '.tar.gz'
    for i in xml_parsed.findall('game'):
        if element == i.get('name'):
            parent = i.find('parent').text
            gamedir = i.find('gamedir').text
## Doings when uploading
    # check if upload parameter is set
    if upload:
        # check if parent directory is set. Some directories do not have a parent part. Such like OlliOlli
        if parent:
            fulldir = "%s/%s/%s" % (my_home, parent, gamedir)
        else:
            fulldir = "%s/%s" % (my_home, gamedir)
        # check if directory of game exists. Otherwhite print an error and exit
        if not os.path.exists(fulldir):
            print "Path \"%s\" doesn't exist." % fulldir
            print "Do you have a local %s of \"%s\"" % (savegame, element)
            sys.exit(2)
#       create temporary directory
        tmp_dir = mkdtemp(prefix="%s." % (element))

        # creating tar file
        print "Creating archive for \"%s\"..." % element
        tar = tarfile.open(tmp_dir + '/' + element + '.tar.gz', "w:gz")
        tar.add(fulldir, arcname=gamedir )
        tar.close()
        # check if sync directory exists. If not create it
        if ( curl_test(my_webdav + '/' + my_sync_dir, my_user, my_password) == 404 ):
            print "Creating the sync directory %s" % my_sync_dir
            curl_mkdir(my_webdav + '/' + my_sync_dir, my_user, my_password)
        # check if directory of specific game exists. If not create it
        if ( curl_test(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password) == 404 ):
            print "Creating the game directory %s" % element
            curl_mkdir(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password)

        # Do the actual curl curl upload
        print "Uploading \"%s\" %s..." % (element, savegame)
        curl_upload(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)

        # removing temporary tar file in tmp directory
        rmtree(tmp_dir)

## Doings when downloading
    # check if download parameter is set
    elif download:
        #check if backup of savestate is available remote
        if ( curl_test(my_webdav + '/' + my_sync_dir + '/' + element + '/' + element + '.tar.gz', my_user, my_password) == 404 ):
            print "Warning: Savestate \"%s\" not found on remote Server \"%s\"" % (element, my_domain)
        # creating temporary directory
        tmp_dir = mkdtemp(prefix="%s." % (element))

        # download the file to temp dir
        print "Downloading the %s of \"%s\"..." % (savegame, element)
        curl_download(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)
        # extract the tar file
        print "Extracting %s of \"%s\"..." % (savegame, element)
        tar = tarfile.open(tmp_dir + '/' + element + '.tar.gz', "r:gz")
        # check if parent variable is set. Change extract path if not set. Usefull for games like OlliOlli
        if parent:
            tar.extractall(path=my_home + '/' + parent)
        else:
            tar.extractall(path=my_home)
        tar.close()
        rmtree(tmp_dir)

sys.exit(0)

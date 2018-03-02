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
import base64
try:
        from io import BytesIO
except ImportError:
        from StringIO import StringIO as BytesIO

# define base variables
script_name = os.path.basename(__file__)
savegame = "savestate"
version = "0.0.1"

# check if script is running as root
if os.getuid() == 0:
    print "%s is not designed to run as root. Please" % script_name
    print "use a normal user account."
    sys.exit(2)

##### functions
def usage():
    print "Usage:"
    print "%s -u [--upload] --games \"$Game1, $Game2\"   uploads the files to your Cloud" % script_name
    print "%s -d [--download] --games \"$Game1, $Game2\" downloads the files from your Cloud" % script_name
    print "%s -u [--upload] --games \"all\"              uploads all available games. Also works for downloads" % script_name
    print "%s -l [--list]                              lists all available games" % script_name
    print "%s -s [--setup]                             Wizard for the configuration file" % script_name
    print "%s -h [--help]                              Shows this help message" % script_name
    print "%s -v [--version]                           Shows %s\'s version" % (script_name, script_name)
    print
    print "Be careful when providing the game list. Seperate every Game with a comma and a whitespace"

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
    config_sync_dir = raw_input("Sync directory for your Cloud [savegames] (can be empty): ")
    config_url_path = raw_input("Webserver Document Root [/owncloud] (can be empty): ")
    config_password = base64.b64encode(config_password)
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
    print "Wrote configuration file \"%s\"." % path_to_config

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
config_path = "%s/.savegame_sync.conf" % my_home

# check if the games.xml is in any of the following pathes
## read bash environment variable
xdg_tmp = os.environ['XDG_DATA_DIRS']
# convert it to a list
xdg_data_dir = xdg_tmp.split(':')

# add for every found list entry and subdirectory with the name of the script
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

# define parameters
try:
    opts, args = getopt.getopt(sys.argv[1:], 'dushlv', ['help', 'list', 'upload', 'download','games=', 'setup', 'version'])
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
            print games
        sys.exit(0)
    elif opt in ('--games'):
        games = arg
        games_enabled = True
    elif opt in ('-s', '--setup'):
        setup_config(config_path)
        sys.exit(0)
    elif opt in ('-v', '--version'):
        print script_name + ' v' + version
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
if games == "all":
    games_array = avail_games
else:
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


# check if configuration file exists on filesystem
if not os.path.exists(config_path):
    print "Configuration file doesn't exist"
    print "Use \"%s --setup\" to create one." % script_name
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

# check optional parameters and set default if not present
if myconfig.has_option('main', 'url_path'):
    my_url_path = myconfig.get('main', 'url_path')
else:
    my_url_path = ""

if myconfig.has_option('main', 'sync_dir'):
    my_sync_dir = myconfig.get('main', 'sync_dir')
else:
    my_sync_dir = "savegames"

# check if password is set. If not, read it from stdin
if myconfig.has_option('main', 'password'):
    my_password = base64.b64decode(myconfig.get('main', 'password'))
else:
    # get password from stdin
    my_password = getpass.getpass("Password for your Cloud: ")

# set domain and user from config parameters
my_domain = myconfig.get('main', 'domain')
my_user = myconfig.get('main', 'user')

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

if upload:
    # check if sync directory exists. If not create it
    if ( curl_test(my_webdav + '/' + my_sync_dir, my_user, my_password) == 404 ):
        print "Creating the sync directory \"%s\"" % my_sync_dir
        add_dir = my_webdav
        for i in my_sync_dir.split('/'):
            add_dir = add_dir + '/' + i
            curl_mkdir(add_dir, my_user, my_password)
        print

for element in games_array:
    my_file_url = my_webdav + '/' + my_sync_dir + '/' + element + '/' + element + '.tar.gz'
    for i in xml_parsed.findall('game'):
        if element == i.get('name'):
            parent = i.find('parent').text
            gamedir = i.find('gamedir').text
## Doings when uploading
    # check if parent directory is set. Some directories do not have a parent part. Such like OlliOlli
    # create temporary directory
    tmp_dir = mkdtemp(prefix="%s." % (element))

    if parent:
        fulldir = "%s/%s/%s" % (my_home, parent, gamedir)
    else:
        fulldir = "%s/%s" % (my_home, gamedir)
    # check if upload parameter is set
    if upload:
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
            # check if directory of specific game exists. If not create it
            if ( curl_test(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password) == 404 ):
                print "Creating the remote game directory \"%s\"..." % element
                curl_mkdir(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password)

            # Do the actual curl curl upload
            print "Uploading \"%s\" %s..." % (element, savegame)
            curl_upload(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)
            print

## Doings when downloading
    # check if download parameter is set
    elif download:
        #check if backup of savestate is available remote
        if ( curl_test(my_webdav + '/' + my_sync_dir + '/' + element + '/' + element + '.tar.gz', my_user, my_password) == 404 ):
            print "Warning: Savestate \"%s\" not found on remote Server \"%s\"." % (element, my_domain)
            print "Cannot sync savestate from Cloud"
            print

        else:
            # download the file to temp dir
            print "Downloading the %s of \"%s\"..." % (savegame, element)
            curl_download(my_file_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)
            # extract the tar file
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

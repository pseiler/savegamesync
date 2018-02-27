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
try:
        from io import BytesIO
except ImportError:
        from StringIO import StringIO as BytesIO

script_name = os.path.basename(__file__)


def usage():
    print "Usage:"
    print "%s -u \"$Game1, $Game2\" uploads the files to your Cloud" % script_name
    print "%s -d \"$Game1, $Game2\" downloads the files from your Cloud" % script_name
    print "                                     to the correct location" 
    print ""
    print "%s -l                  lists all available games" % script_name
    print "%s -s                  Wizard for the configuration file" % script_name
    print "%s -h                  Shows this help message" % script_name

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


#usage()

avail_games = []
xml_parsed = xml.etree.ElementTree.parse('games.xml').getroot()
for game in xml_parsed.findall('game'):
    avail_games.append(game.get('name'))


my_home = os.environ['HOME']

#games_list = xml_parsed.findall('game')
#print xml_parsed.findall('game')
config_path = "config.cfg"
myconfig = ConfigParser.ConfigParser()
myconfig.read(config_path)
#print myconfig.get(main, )
#print myconfig.has_section('main')
if not myconfig.has_section('main'):
    print "No section [\"main\"] in config"
    sys.exit(2)

if not myconfig.has_option('main', 'domain'):
    print "No attribute \"domain\""
    sys.exit(2)
elif not myconfig.has_option('main', 'user'):
    print "No attribute \"user\""
    sys.exit(2)
elif not myconfig.has_option('main', 'password'):
    print "No attribute \"password\""
    sys.exit(2)

if myconfig.has_option('main', 'url_path'):
    my_url_path = myconfig.get('main', 'url_path')
else:
    my_url_path = ""

if myconfig.has_option('main', 'sync_dir'):
    my_sync_dir = myconfig.get('main', 'sync_dir')
else:
    my_sync_dir = "savegames"

my_domain = myconfig.get('main', 'domain')
my_user = myconfig.get('main', 'user')
my_password = myconfig.get('main', 'password')

my_webdav = "https://%s/%s/remote.php/dav/files/%s" % (my_domain, my_url_path, my_user)
#print my_webdav

#config.read(['site.cfg', os.path.expanduser('~/.myapp.cfg')])

#print xml_parsed.findall('game')


#game_list = xml_parsed.find('game')

download = "no"
upload = "no"
games_enabled = "no"

# define parameters
try:
    opts, args = getopt.getopt(sys.argv[1:], 'dushl', ['help', 'list', 'upload', 'download','games=', 'setup'])
except getopt.GetoptError:
    print "Wrong arguments given."
    usage()
    sys.exit(2)
 
for opt, arg in opts:
    if opt in ('-h', '--help'):
        print "%s provides savegame sync features for your owncloud/nextcloud instance" % script_name
        usage()
        sys.exit(2)
    elif opt in ('-u', '--upload'):
        upload = "yes"
    elif opt in ('-d', '--download'):
        download = "yes"
    elif opt in ('-l', '--list'):
        print "Available Games"
        print "---------------"
        for games in xml_parsed.findall('game'):
            print games.get('name')
        sys.exit(0)
    elif opt in ('--games'):
        games = arg
        games_enabled = "yes"
    elif opt in ('-s', '--setup'):
        print "to be implemented"
        sys.exit(2)
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

if (download == "no" and upload == "no"):
    print "No arguments given. Please use at least -u or -d and --games\n"
    usage()       
    sys.exit(2)
elif (download == "yes" and upload == "yes"):
    print "Both upload and download argument given. Please only use one of them"
    usage()
    sys.exit(2)
#for game in xml_parsed.findall('game'):
    #print game.get('name')
for element in games_array:
    for i in xml_parsed.findall('game'):
        if element == i.get('name'):
            parent = i.find('parent').text
            gamedir = i.find('gamedir').text
    fulldir = "%s/%s/%s" % (my_home, parent, gamedir)

    if (upload == "yes"):
        if not os.path.exists(fulldir):
            print "Path \"%s\" doesn't exist." % fulldir
            print "Do you have a local savestate of for %s" % element
            sys.exit(2)
#       create temporary directory
        tmp_dir = mkdtemp(prefix="%s." % (element))

        # creating tar file
        print "Creating archive for \"%s\"..." % element
        tar = tarfile.open(tmp_dir + '/' + element + '.tar.gz', "w:gz")
        tar.add(my_home + '/' + parent + '/' + gamedir, arcname=gamedir )
        tar.close()
        print "%s/%s" % (my_webdav, my_sync_dir)
#        print "%s/%s.tar.gz" % (tmp_dir, element)
#        filesize = os.path.getsize(tmp_dir + '/' + element + '.tar.gz')
        if (curl_test(my_webdav + '/' + my_sync_dir, my_user, my_password) == 404 ):
            print "Creating the sync directory %s" % my_sync_dir
            curl_mkdir(my_webdav + '/' + my_sync_dir, my_user, my_password)
        if (curl_test(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password) == 404 ):
            print "Creating the game directory %s" % element
            curl_mkdir(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password)

#        print "Create remote Game directory for \"%s\"." % element
#        curl_mkdir(my_webdav + '/' + my_sync_dir + '/' + element, my_user, my_password)
#       Do the actual curl upload call
        print "Uploading \"%s\" savegame..." % element
        my_upload_url = my_webdav + '/' + my_sync_dir + '/' + element + '/' + element + '.tar.gz'
        curl_upload(my_upload_url, tmp_dir + '/' + element + '.tar.gz', my_user, my_password)

        # removing temporary tar file in tmp directory
        rmtree(tmp_dir)

    elif (download == "yes"):
        print "not implemented yet"



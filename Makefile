VERSION = 3.02
PREFIX=/usr/local
DESTDIR=
SCRIPT=savegame_sync
bindir=$(PREFIX)/bin

install:
	        install -D -m0755 $(SCRIPT).sh $(DESTDIR)$(bindir)/$(SCRIPT)
uninstall:
			rm $(DESTDIR)$(bindir)/$(SCRIPT)

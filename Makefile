VERSION = 3.02
PREFIX=/usr/local
DESTDIR=
NAME=savegame_sync
bindir=$(PREFIX)/bin
sharedir=$(PREFIX)/share
games=games.xml

install:
	        install -D -m0755 $(NAME).py $(DESTDIR)$(bindir)/$(NAME)
	        install -D -m0644 $(games) $(DESTDIR)$(sharedir)/$(NAME)/$(games)
uninstall:
			rm $(DESTDIR)$(bindir)/$(NAME)
	        rm -r $(DESTDIR)$(sharedir)/$(NAME)

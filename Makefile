
PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
MANDIR ?= $(PREFIX)/man
SHAREDIR ?= $(PREFIX)/share
PYTHON ?= /usr/bin/env python

v_qq_dl: src/v_qq_dl/*.py
	cd src && zip --quiet ../v_qq_dl v_qq_dl/*.py
	zip --quiet --junk-paths v_qq_dl src/v_qq_dl/__main__.py
	echo '#!$(PYTHON)' > v_qq_dl
	cat v_qq_dl.zip >> v_qq_dl
	rm v_qq_dl.zip
	chmod a+x v_qq_dl

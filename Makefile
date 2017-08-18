
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

clean:
	rm proxy.json bin/*.json bin/*.txt bin/*.mp4 bin/*.aria2

readme:
	COLUMNS=80 $(PYTHON) src/v_qq_dl/__main__.py --help | $(PYTHON) src/devscripts/make_readme.py

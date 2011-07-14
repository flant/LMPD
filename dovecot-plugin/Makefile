# include config file if present
CONFIG ?= .config
-include $(CONFIG)
CFLAGSORIG := $(CFLAGS)
DOVECOT ?= /usr/include/dovecot
PLUGINNAME ?= antispam
-include $(DOVECOT)/dovecot-config
INSTALLDIR ?= $(moduledir)/imap
# Kill CFLAGS from dovecot-config
CFLAGS := $(CFLAGSORIG)

# includes/flags we need for building a dovecot plugin
INCS += -DHAVE_CONFIG_H
INCS += -I$(DOVECOT)/
INCS += -I$(DOVECOT)/src/
INCS += -I$(DOVECOT)/src/lib/
INCS += -I$(DOVECOT)/src/lib-storage/
INCS += -I$(DOVECOT)/src/lib-mail/
INCS += -I$(DOVECOT)/src/lib-imap/
INCS += -I$(DOVECOT)/src/lib-dict/
INCS += -I$(DOVECOT)/src/lib-index/
INCS += -I$(DOVECOT)/src/imap/

# output name
LIBRARY_NAME ?= lib90_$(PLUGINNAME)_plugin.so
objs = antispam-storage.o antispam-plugin.o debug.o
objs += dspam-exec.o signature-log.o crm114-exec.o pipe.o spool2dir.o signature.o

# main make rules
LOCALCFLAGS += -fPIC -shared -Wall -Wextra -DPLUGINNAME=$(PLUGINNAME)
CC ?= cc
HOSTCC ?= cc

all: $(LIBRARY_NAME)

antispam-storage.o: antispam-storage.c antispam-storage-*.c antispam-plugin.h dovecot-version.h
	$(CC) -c $(CFLAGS) $(LOCALCFLAGS) $(INCS) -o $@ $<

%.o: %.c antispam-plugin.h dovecot-version.h antispam-version.h
	$(CC) -c $(CFLAGS) $(LOCALCFLAGS) $(INCS) -o $@ $<

$(LIBRARY_NAME): $(objs)
	$(CC) $(CFLAGS) $(LOCALCFLAGS) $(INCS) $(objs) -o $(LIBRARY_NAME) $(LDFLAGS)

dovecot-version: dovecot-version.c
	$(HOSTCC) $(INCS) -o dovecot-version dovecot-version.c

dovecot-version.h: dovecot-version
	./dovecot-version > dovecot-version.h

antispam-version.h: version.sh
	./version.sh > antispam-version.h


clean:
	rm -f *.so *.o *~ dovecot-version dovecot-version.h antispam-version.h

install: all checkinstalldir
	install -p -m 0755 $(LIBRARY_NAME) $(DESTDIR)$(INSTALLDIR)/

checkinstalldir:
	@if [ ! -d "$(DESTDIR)$(INSTALLDIR)/" ] ; then \
		echo "Installation directory $(DESTDIR)$(INSTALLDIR)/ doesn't exist," ; \
		echo "run make install INSTALLDIR=..." ; \
		exit 2 ; \
	fi

all:
	touch stamp > /dev/null

install: all
	cp -r lmpd $(DESTDIR)/usr/lib/ 
	cp lmp $(DESTDIR)/usr/bin/lmpd
	cp config/lmpd.yaml $(DESTDIR)/etc/postfix

clean:
	rm -f stamp > /dev/null

uninstall:
	rm -rf $(DESTDIR)/usr/lib/lmpd
	rm -f $(DESTDIR)/usr/bin/lmpd

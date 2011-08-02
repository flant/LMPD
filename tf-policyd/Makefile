all:
	touch stamp > /dev/null

install: all
	mkdir -p $(DESTDIR)/usr/lib/python2.6/
	mkdir -p $(DESTDIR)/usr/sbin/
	cp -r tf_policyd $(DESTDIR)/usr/lib/python2.6/ 
	cp tf_policy $(DESTDIR)/usr/sbin/tf_policyd

clean:
	rm -f stamp > /dev/null

uninstall:
	rm -rf /usr/lib/python2.6/tf_policyd
	rm -f /usr/sbin/tf_policyd

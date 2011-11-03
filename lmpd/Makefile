all:
	touch stamp > /dev/null

install: all
	cp -r tfpolicyd $(DESTDIR)/usr/lib/python2.6/ 
	cp tfpolicy $(DESTDIR)/usr/sbin/tfpolicyd
	cp config/tfpolicyd.yaml $(DESTDIR)/etc/postfix

clean:
	rm -f stamp > /dev/null

uninstall:
	rm -rf /usr/lib/python2.6/tfpolicyd
	rm -f /usr/sbin/tfpolicyd

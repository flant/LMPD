#!/usr/bin/env python
import socket

k = 'request=smtpd_access_policy\nprotocol_state=RCPT\nprotocol_name=ESMTP\nclient_address=192.168.1.1\nclient_name=router.loc\nreverse_client_name=router.loc\nhelo_name=mail.klan-hub.ru\nsender=abc@klan-hub.ru\nrecipient=mariner@klan-hub.ru\nrecipient_count=0\nqueue_id=\ninstance=b4e.4dfb48e2.95e42.0\nsize=2036\netrn_domain=\nstress=\nsasl_method=\nsasl_username=\nsasl_sender=\nccert_subject=\nccert_issuer=\nccert_fingerprint=\nencryption_protocol=\nencryption_cipher=\nencryption_keysize=0\n\n'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 7000))
s.send(k)
data = s.recv(1024)
s.close()
print 'Received', repr(data)

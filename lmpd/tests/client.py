#!/usr/bin/env python
import socket

oRegs=0

k = 'request=smtpd_access_policy\nprotocol_state=RCPT\nprotocol_name=ESMTP\nclient_address=192.168.1.1\nclient_name=router.loc\nreverse_client_name=router.loc\nhelo_name=mail.klan-hub.ru\nsender=nikolay.bogdanov@2014.auditory.ru\nrecipient=bog1990@mail.ru\nrecipient_count=0\nqueue_id=\ninstance=b4e.4dfb48e2.95e42.0\nsize=2036\netrn_domain=\nstress=\nsasl_method=\nsasl_username=nikolay.bogdanov@2014.auditory.ru\nsasl_sender=\nccert_subject=\nccert_issuer=\nccert_fingerprint=\nencryption_protocol=\nencryption_cipher=\nencryption_keysize=0\n\n'

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/var/spool/postfix/private/policy.sock")
s.send(k)
s.close()

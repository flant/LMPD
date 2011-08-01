#ifndef _ANTISPAM_SIGNATURE_H
#define _ANTISPAM_SIGNATURE_H

#include "lib.h"
#include "client.h"
#include <stdint.h>

#include "antispam-plugin.h"

struct siglist {
	struct siglist *next;
	char *sig;
	char *from;
	char *to;
	uint8_t sig_bool;
	enum classification wanted;
};

void signature_init(void);
int signature_extract_to_list(struct mailbox_transaction_context *t,
			      struct mail *mail, struct siglist **list,
			      enum classification wanted);
int signature_extract(struct mailbox_transaction_context *t,
		      struct mail *mail, const char **signature);
void signature_list_free(struct siglist **list);

extern const char *signature_hdr;

#endif /* _ANTISPAM_SIGNATURE_H */

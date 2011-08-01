#ifndef _ANTISPAM_SIGNATURE_H
#define _ANTISPAM_SIGNATURE_H

#include "lib.h"
#include "client.h"
#include <stdint.h>

#include "antispam-plugin.h"

struct tfsiglist {
	struct tfsiglist *next;
	char *sig;
	char *from;
	char *to;
	uint8_t sig_bool;
	enum classification wanted;
};

void tfsignature_init(void);
int tfsignature_extract_to_list(struct mailbox_transaction_context *t,
			      struct mail *mail, struct tfsiglist **list,
			      enum classification wanted);
int tfsignature_extract(struct mailbox_transaction_context *t,
		      struct mail *mail, const char **signature);
void tfsignature_list_free(struct tfsiglist **list);

extern const char *tfsignature_hdr;

#endif /* _ANTISPAM_SIGNATURE_H */

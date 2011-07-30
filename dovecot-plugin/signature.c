
#include <stdlib.h>
#include "antispam-plugin.h"
#include "signature.h"
#include "mail-storage-private.h"

const char *signature_hdr = "X-DSPAM-Signature";
const char *from_hdr = "From";
const char *to_hdr = "Delivered-To";
static int signature_nosig_ignore = 0;

void signature_init(void)
{
	const char *tmp = get_setting("SIGNATURE");
	if (tmp)
		signature_hdr = tmp;
	debug("signature header line is \"%s\"\n", signature_hdr);

	tmp = get_setting("SIGNATURE_MISSING");
	if (!tmp)
		tmp = "error";
	if (strcmp(tmp, "move") == 0) {
		signature_nosig_ignore = 1;
		debug("will silently move mails with missing signature\n");
	} else if (strcmp(tmp, "error") != 0) {
		debug("invalid signature_missing setting '%s', ignoring\n", tmp);
	}
}

int signature_extract_to_list(struct mailbox_transaction_context *t,
			      struct mail *mail, struct siglist **list,
			      enum classification wanted)
{
	const char *const *signatures;

	const char *const *from;
	const char *const *to;

	struct siglist *item;

	signatures = get_mail_headers(mail, signature_hdr); //Reference to this func
	from = get_mail_headers(mail, from_hdr);
	to = get_mail_headers(mail, to_hdr);
	if (!signatures || !signatures[0]) {
		if (!signature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "antispam signature not found");
			return -1;
		} else {
			return 0;
		}
	}

	if (!to || !to[0]) {
		if (!signature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "recipient not found");
			return -1;
		} else {
			return 0;
		}
	}

	if (!from || !from[0]) {
		if (!signature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "sender not found");
			return -1;
		} else {
			return 0;
		}
	}

	while (signatures[1])
		signatures++;

	//while (from[1])
	//	from++;

	//while (to[1])
	//	to++;

	item = i_new(struct siglist, 1);
	item->next = *list;
	item->wanted = wanted;
	item->sig = i_strdup(signatures[0]);
	item->from = i_strdup(from[0]);
	item->to = i_strdup(to[0]);

	*list = item;

	return 0;
}

int signature_extract(struct mailbox_transaction_context *t,
		      struct mail *mail, const char **signature)
{
	const char *const *signatures;

	signatures = get_mail_headers(mail, signature_hdr);

	if (!signatures || !signatures[0]) {
		if (!signature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "antispam signature not found");
			return -1;
		} else {
			*signature = NULL;
			return 0;
		}
	}

	while (signatures[1])
		signatures++;

	*signature = signatures[0];

	return 0;
}

void signature_list_free(struct siglist **list)
{
	struct siglist *item, *next;

	i_assert(list);

	item = *list;

	while (item) {
		next = item->next;
		i_free(item->sig);
		i_free(item->from);
		i_free(item->to);
		i_free(item);
		item = next;
		if (item)
			next = item->next;
	}
}

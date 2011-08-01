
#include <stdlib.h>
#include "antispam-plugin.h"
#include "tfsignature.h"
#include "mail-storage-private.h"

const char *tfsignature_hdr = "X-DSPAM-Signature";
const char *tffrom_hdr = "From";
const char *tfto_hdr = "Delivered-To";
static int tfsignature_nosig_ignore = 0;

void tfsignature_init(void)
{
	const char *tmp = get_setting("SIGNATURE");
	if (tmp)
		tfsignature_hdr = tmp;
	debug("signature header line is \"%s\"\n", tfsignature_hdr);

	tmp = get_setting("SIGNATURE_MISSING");
	if (!tmp)
		tmp = "error";
	if (strcmp(tmp, "move") == 0) {
		tfsignature_nosig_ignore = 1;
		debug("will silently move mails with missing signature\n");
	} else if (strcmp(tmp, "error") != 0) {
		debug("invalid signature_missing setting '%s', ignoring\n", tmp);
	}
}

int tfsignature_extract_to_list(struct mailbox_transaction_context *t,
			      struct mail *mail, struct tfsiglist **list,
			      enum classification wanted)
{
	const char *const *signatures;

	const char *const *from;
	const char *const *to;
	uint8_t sig_bool;

	struct tfsiglist *item;

	signatures = get_mail_headers(mail, tfsignature_hdr); //Reference to this func
	from = get_mail_headers(mail, tffrom_hdr);
	to = get_mail_headers(mail, tfto_hdr);
	if (!signatures || !signatures[0]) {
/*		if (!signature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "antispam signature not found");
			return -1;
		} else {
			return 0;
		} */
		sig_bool = 0;
	} else {
		sig_bool = 1;
	}

	if (!to || !to[0]) {
		if (!tfsignature_nosig_ignore) {
			mail_storage_set_error(t->box->storage,
					       ME(NOTPOSSIBLE)
					       "recipient not found");
			return -1;
		} else {
			return 0;
		}
	}

	if (!from || !from[0]) {
		if (!tfsignature_nosig_ignore) {
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

	item = i_new(struct tfsiglist, 1);
	item->next = *list;
	item->wanted = wanted;
	item->sig = i_strdup(signatures[0]);
	item->from = i_strdup(from[0]);
	item->sig_bool = sig_bool;
	item->to = i_strdup(to[0]);

	*list = item;

	return 0;
}

int tfsignature_extract(struct mailbox_transaction_context *t,
		      struct mail *mail, const char **signature)
{
	const char *const *signatures;

	signatures = get_mail_headers(mail, tfsignature_hdr);

	if (!signatures || !signatures[0]) {
		if (!tfsignature_nosig_ignore) {
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

void tfsignature_list_free(struct tfsiglist **list)
{
	struct tfsiglist *item, *next;

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

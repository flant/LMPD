/*
 * mailing backend for dovecot antispam plugin
 *
 * Copyright (C) 2008       Steffen Kaiser <skdovecot@smail.inf.fh-brs.de>
 * this backend "spool2dir" bases on "mailtrain" backend of
 * Copyright (C) 2007       Johannes Berg <johannes@sipsolutions.net>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License Version 2 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
 */


/*
 * spool2dir antispam backend / plugin
 *
 * Any modification of SPAM status is recorded into a directory.
 *
 * Configuration
 *
 * Via settings similiar to the other antispam backends
 *	antispam_spool2dir_spam :- filename tempate for SPAM messages
 *	antispam_spool2dir_notsam :- filename tempate for HAM messages
 *
 * The templates _must_ provide two arguments:
 *   1. %%lu - the current unix time (lowercase L, lowercase U)
 *   2. %%lu - a counter to create different temporary files
 * Note: The %-sign must be given two times to protect agains
 *  the expansion by Dovecot itself. You can put any legal
 *  format modification character of C's printf() function between
 *  '%%' and 'lu'.
 *
 * e.g.:
 *	antispam_spool2dir_spam = /tmp/spamspool/%%020lu-%%05lu-%u-S
 *	antispam_spool2dir_ham  = /tmp/spamspool/%%020lu-%%05lu-%u-H
 *
 * This example will spool the messages into the directory
 * /tmp/spamspool. The individual files start with 20 digits,
 * followe by a dash, 5 digits, the current username and S or H,
 * indicating Spam or Ham messages.
 * The first %%lu placeholder is replace by the current unix time,
 * the second %%lu with the counter. That way, if the same user
 * trains the same message twice, the filename indicates the order
 * in which it was done. So if the message was trained as SPAM first,
 * as HAM later, HAM superceeds SPAM.
 *
 * Operation
 *
 * When the antispam plugin identifies detects a SPAM status change,
 * e.g. moving/copying a message from any antispam_spam folder into
 * a folder _not_ listed in antispam_spam or antispam_trash, this
 * backend spools the complete message into antispam_mail_basedir.
 * If there is an error copying _all_ messages around, old spools
 * are kept, but the current one is deleted. For instance, if the
 * user is copying 15 messages, but only 10 succeed, the 10 would
 * be usually deleted. In this backend there is no rollback of
 * successfully spooled message, only the failed message is
 * deleted.
 *
 * Possible usage models
 *
 * A)
 *   I use spool2dir for training the Bayes database as follows:
 *
 *   Every 10 seconds a service invokes the training program, unless
 *   it already runs.
 *
 *   The training progran reads the content of the spool directory, sorts
 *   the filenames alphanumerically, waits two seconds to allow any current
 *   spool2dir processes to finish currently open files.
 *   Then one message at a time is read and identified, if it contains
 *   local modifications, e.g. user-visible SPAM reports, which are removed.
 *   Furthermore, reports of untrustworthy people are discarded.
 *   This process continues until either all messages are processed or
 *   the next message would have another SPAM report type (HAM or SPAM). The
 *   file names of the messages processed til now are passed to the Bayes
 *   trainer to be processed within one run. Then those messages are removed.
 *
 * B)
 *
 *   An Inotify server watches the spamspool directory and passes the messages
 *   to spamd. No need for the filenames to indicate the order anymore, unless
 *   the inotify server is not fast enough.
 */

#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>

#include "lib.h"
#include "mail-storage-private.h"
#include "ostream.h"
#include "istream.h"

#include "antispam-plugin.h"

static const char *spamspool = NULL;
static const char * hamspool = NULL;

struct antispam_transaction_context {
	int count;
};


static void backend_rollback(struct antispam_transaction_context *ast)
{
	i_free(ast);
}

static int backend_commit(struct mailbox_transaction_context *ctx __attr_unused__,
			  struct antispam_transaction_context *ast)
{
	i_free(ast);

	return 0;
}

static int backend_handle_mail(struct mailbox_transaction_context *t,
			       struct antispam_transaction_context *ast,
			       struct mail *mail, enum classification wanted)
{
	struct istream *mailstream;
	struct ostream *outstream;
	int ret = -1;
	const char *dest, *buf;
	const unsigned char *beginning;
	size_t size;
	int fd = -1;

	i_assert(ast);

	switch (wanted) {
	case CLASS_SPAM:
		dest = spamspool;
		break;
	case CLASS_NOTSPAM:
		dest =  hamspool;
		break;
	default:	/* cannot handle this */
		return -1;
	}

	if(!dest) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "antispam plugin / spool2dir backend not configured");
		return -1;
	}

	mailstream = get_mail_stream(mail);
	if (!mailstream) {
		mail_storage_set_error(t->box->storage,
				       ME(EXPUNGED)
				       "Failed to get mail contents");
		return -1;
	}

	t_push();

	/* atomically create a _new_ file */
	while (ast->count <= 9999) {
		buf = t_strdup_printf(dest, (long)time(0), (long)++ast->count);
		fd = open(buf, O_CREAT | O_EXCL | O_WRONLY, 0600);
		if (fd >= 0 || errno != EEXIST)
			break;
		/* current filename in buf already exists, zap it */
		t_pop();
		t_push();
		/* buf is invalid now! */
	}

	if (fd < 0) {
		debug("spool2dir backend: Failed to create spool file %s: %s\n",
		      dest, strerror(errno));
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
					   "Failed to create spool file");
		goto out;
	}

	/* buf still points to allocated memory, because fd >= 0 */

	outstream = o_stream_create_from_fd(fd, t->box->pool);
	if (!outstream) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to stream spool file");
		goto out_close;
	}

	if (i_stream_read_data(mailstream, &beginning, &size, 5) < 0 ||
	    size < 5) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to read mail beginning");
		goto failed_to_copy;
	}

	/* "From "? skip line */
	if (memcmp("From ", beginning, 5) == 0)
		i_stream_read_next_line(mailstream);

	if (o_stream_send_istream(outstream, mailstream) < 0) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to copy to spool file");
		goto failed_to_copy;
	}

	ret = 0;

 failed_to_copy:
	o_stream_destroy(&outstream);
 out_close:
	close(fd);
	if (ret)
		unlink(buf);
 out:
	t_pop();

	return ret;
}

static void backend_init(pool_t pool __attr_unused__)
{
	spamspool = get_setting("SPOOL2DIR_SPAM");
	if (spamspool)
		debug("spool2dir spamspool %s\n", spamspool);

	hamspool = get_setting("SPOOL2DIR_NOTSPAM");
	if (hamspool)
		debug("spool2dir hamspool %s\n", hamspool);
}

static struct antispam_transaction_context *
backend_start(struct mailbox *box __attr_unused__)
{
	struct antispam_transaction_context *ast;

	ast = i_new(struct antispam_transaction_context, 1);

	ast->count = 0;

	return ast;
}


static void backend_exit(void)
{
}

struct backend spool2dir_backend = {
	.init = backend_init,
	.exit = backend_exit,
	.handle_mail = backend_handle_mail,
	.start = backend_start,
	.rollback = backend_rollback,
	.commit = backend_commit,
};

/*
 * mailing backend for dovecot antispam plugin
 *
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

#include <unistd.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <fcntl.h>

#include "lib.h"
#include "dict.h"
#include "mail-storage-private.h"
#include "ostream.h"
#include "istream.h"

#include "antispam-plugin.h"

static const char *spam_arg = NULL;
static const char *ham_arg = NULL;
static const char *pipe_binary = "/usr/sbin/sendmail";
static const char *tmpdir = "/tmp";
static char **extra_args = NULL;
static int extra_args_num = 0;

static int run_pipe(int mailfd, enum classification wanted)
{
	const char *dest;
	pid_t pid;
	int status;

	switch (wanted) {
	case CLASS_SPAM:
		dest = spam_arg;
		break;
	case CLASS_NOTSPAM:
		dest = ham_arg;
		break;
	}

	if (!dest)
		return -1;

	pid = fork();

	if (pid == -1)
		return -1;

	debug("running mailtrain backend program %s", pipe_binary);

	if (pid) {
		if (waitpid(pid, &status, 0) == -1)
			return -1;
		if (!WIFEXITED(status))
			return -1;
		return WEXITSTATUS(status);
	} else {
		char **argv;
		int sz = sizeof(char *) * (2 + extra_args_num + 1);
		int i, fd;

		argv = i_malloc(sz);
		memset(argv, 0, sz);

		argv[0] = (char *) pipe_binary;

		for (i = 0; i < extra_args_num; i++)
			argv[i + 1] = (char *) extra_args[i];

		argv[i + 1] = (char *) dest;

		dup2(mailfd, 0);
		fd = open("/dev/null", O_WRONLY);
		dup2(fd, 1);
		dup2(fd, 2);
		close(fd);
		execv(pipe_binary, argv);
		_exit(1);
		/* not reached */
		return -1;
	}
}

struct antispam_transaction_context {
	char *tmpdir;
	int count;
	int tmplen;
};

static struct antispam_transaction_context *
backend_start(struct mailbox *box __attr_unused__)
{
	struct antispam_transaction_context *ast;
	char *tmp;

	ast = i_new(struct antispam_transaction_context, 1);

	ast->count = 0;

	tmp = i_strconcat(tmpdir, "/antispam-mail-XXXXXX", NULL);

	ast->tmpdir = mkdtemp(tmp);
	if (!ast->tmpdir)
		i_free(tmp);
	else
		ast->tmplen = strlen(ast->tmpdir);

	return ast;
}

static int process_tmpdir(struct mailbox_transaction_context *ctx,
			  struct antispam_transaction_context *ast)
{
	int cnt = ast->count;
	int fd;
	char *buf;
	enum classification wanted;
	int rc = 0;

	t_push();

	buf = t_malloc(20 + ast->tmplen);

	while (rc == 0 && cnt > 0) {
		cnt--;
		i_snprintf(buf, 20 + ast->tmplen - 1, "%s/%d",
			   ast->tmpdir, cnt);

		fd = open(buf, O_RDONLY);
		read(fd, &wanted, sizeof(wanted));

		if ((rc = run_pipe(fd, wanted))) {
			mail_storage_set_error(ctx->box->storage,
					       ME(TEMP)
					       "failed to send mail");
			debug("run program failed with exit code %d\n", rc);
			rc = -1;
		}

		close(fd);
	}

	t_pop();

	return rc;
}

static void clear_tmpdir(struct antispam_transaction_context *ast)
{
	char *buf;

	t_push();

	buf = t_malloc(20 + ast->tmplen);

	while (ast->count > 0) {
		ast->count--;
		i_snprintf(buf, 20 + ast->tmplen - 1, "%s/%d",
			   ast->tmpdir, ast->count);
		unlink(buf);
	}
	rmdir(ast->tmpdir);

	t_pop();
}

static void backend_rollback(struct antispam_transaction_context *ast)
{
	if (ast->tmpdir) {
		/* clear it! */
		clear_tmpdir(ast);
		i_free(ast->tmpdir);
	}

	i_free(ast);
}

static int backend_commit(struct mailbox_transaction_context *ctx,
			  struct antispam_transaction_context *ast)
{
	int ret;

	if (!ast->tmpdir) {
		i_free(ast);
		return 0;
	}

	ret = process_tmpdir(ctx, ast);

	clear_tmpdir(ast);

	i_free(ast->tmpdir);
	i_free(ast);

	return ret;
}

static int backend_handle_mail(struct mailbox_transaction_context *t,
			       struct antispam_transaction_context *ast,
			       struct mail *mail, enum classification wanted)
{
	struct istream *mailstream;
	struct ostream *outstream;
	int ret;
	char *buf;
	const unsigned char *beginning;
	size_t size;
	int fd;

	if (!ast->tmpdir) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to initialise temporary dir");
		return -1;
	}

	if (!ham_arg || !spam_arg) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "antispam plugin not configured");
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

	buf = t_malloc(20 + ast->tmplen);
	i_snprintf(buf, 20 + ast->tmplen - 1, "%s/%d", ast->tmpdir, ast->count);

	fd = creat(buf, 0600);
	if (fd < 0) {
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to create temporary file");
		ret = -1;
		goto out;
	}

	ast->count++;

	outstream = o_stream_create_from_fd(fd, t->box->pool);
	if (!outstream) {
		ret = -1;
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to stream temporary file");
		goto out_close;
	}

	if (o_stream_send(outstream, &wanted, sizeof(wanted))
			!= sizeof(wanted)) {
		ret = -1;
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to write marker to temp file");
		goto failed_to_copy;
	}

	if (i_stream_read_data(mailstream, &beginning, &size, 5) < 0 ||
	    size < 5) {
		ret = -1;
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to read mail beginning");
		goto failed_to_copy;
	}

	/* "From "? skip line */
	if (memcmp("From ", beginning, 5) == 0)
		i_stream_read_next_line(mailstream);

	if (o_stream_send_istream(outstream, mailstream) < 0) {
		ret = -1;
		mail_storage_set_error(t->box->storage,
				       ME(NOTPOSSIBLE)
				       "Failed to copy to temporary file");
		goto failed_to_copy;
	}

	ret = 0;

 failed_to_copy:
	o_stream_destroy(&outstream);
 out_close:
	close(fd);
 out:
	t_pop();

	return ret;
}

static void backend_init(pool_t pool __attr_unused__)
{
	const char *tmp;
	int i;

	tmp = get_setting("PIPE_PROGRAM_SPAM_ARG");
	if (!tmp)
		tmp = get_setting("MAIL_SPAM");
	if (tmp) {
		spam_arg = tmp;
		debug("pipe backend spam argument = %s\n", tmp);
	}

	tmp = get_setting("PIPE_PROGRAM_NOTSPAM_ARG");
	if (!tmp)
		tmp = get_setting("MAIL_NOTSPAM");
	if (tmp) {
		ham_arg = tmp;
		debug("pipe backend not-spam argument = %s\n", tmp);
	}

	tmp = get_setting("PIPE_PROGRAM");
	if (!tmp)
		tmp = get_setting("MAIL_SENDMAIL");
	if (tmp) {
		pipe_binary = tmp;
		debug("pipe backend program = %s\n", tmp);
	}

	tmp = get_setting("PIPE_PROGRAM_ARGS");
	if (!tmp)
		tmp = get_setting("MAIL_SENDMAIL_ARGS");
	if (tmp) {
		extra_args = p_strsplit(pool, tmp, ";");
		extra_args_num = str_array_length(
					(const char *const *)extra_args);
		for (i = 0; i < extra_args_num; i++)
			debug("pipe backend program arg[%d] = %s\n",
			      i, extra_args[i]);
	}

	tmp = get_setting("PIPE_TMPDIR");
	if (!tmp)
		tmp = get_setting("MAIL_TMPDIR");
	if (tmp)
		tmpdir = tmp;
	debug("pipe backend tmpdir %s\n", tmpdir);
}

static void backend_exit(void)
{
}

struct backend pipe_backend = {
	.init = backend_init,
	.exit = backend_exit,
	.handle_mail = backend_handle_mail,
	.start = backend_start,
	.rollback = backend_rollback,
	.commit = backend_commit,
};

/*
 * crm114 backend for dovecot antispam plugin
 *
 * Copyright (C) 2004-2007  Johannes Berg <johannes@sipsolutions.net>
 *                    2006  Frank Cusack
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
#include "mail-storage-private.h"

#include "antispam-plugin.h"
#include "signature.h"

static const char *reaver_binary = "/bin/false";
static char **extra_args = NULL;
static int extra_args_num = 0;

static int call_reaver(const char *signature, enum classification wanted)
{
	pid_t pid;
	const char *class_arg;
	int pipes[2];

	switch (wanted) {
	case CLASS_NOTSPAM:
		class_arg = "--good";
		break;
	case CLASS_SPAM:
		class_arg = "--spam";
		break;
	}

	/*
	 * For reaver stdin, it wants to read a full message but
	 * really only needs the signature.
	 */
	if (pipe(pipes))
		return -1;

	pid = fork();
	if (pid < 0)
		return -1;

	if (pid) {
		int status;

		close(pipes[0]);

		/*
		 * Reaver wants the mail but only needs the cache ID
		 */
		write(pipes[1], signature_hdr, strlen(signature_hdr));
		write(pipes[1], ": ", 2);
		write(pipes[1], signature, strlen(signature));
		write(pipes[1], "\r\n\r\n", 4);
		close(pipes[1]);

		/*
		 * Wait for reaver
		 */
		waitpid(pid, &status, 0);
		if (!WIFEXITED(status))
			return 1;

		return WEXITSTATUS(status);
	} else {
		int fd = open("/dev/null", O_RDONLY);
		char **argv;
		/* 2 fixed, extra, terminating NULL */
		int sz = sizeof(char *) * (2 + extra_args_num + 1);
		int i;

		argv = i_malloc(sz);
		memset(argv, 0, sz);

		close(0);
		close(1);
		close(2);
		/* see above */
		close(pipes[1]);

		if (dup2(pipes[0], 0) != 0)
			exit(1);
		close(pipes[0]);

		if (dup2(fd, 1) != 1)
			exit(1);
		if (dup2(fd, 2) != 2)
			exit(1);
		close(fd);

		argv[0] = (char *)reaver_binary;
		argv[1] = (char *)class_arg;

		for (i = 0; i < extra_args_num; i++)
			argv[i + 2] = (char *)extra_args[i];

		debugv(argv);

		execv(reaver_binary, argv);
		/* fall through if reaver can't be found */
                debug("executing %s failed: %d (uid=%d, gid=%d)",
			reaver_binary, errno, getuid(), getgid());
		exit(127);
		/* not reached */
		return -1;
	}
}

struct antispam_transaction_context {
	struct siglist *siglist;
};

static struct antispam_transaction_context *
backend_start(struct mailbox *box __attr_unused__)
{
	struct antispam_transaction_context *ast;

	ast = i_new(struct antispam_transaction_context, 1);
	ast->siglist = NULL;
	return ast;
}

static void backend_rollback(struct antispam_transaction_context *ast)
{
	signature_list_free(&ast->siglist);
	i_free(ast);
}

static int backend_commit(struct mailbox_transaction_context *ctx,
		   struct antispam_transaction_context *ast)
{
	struct siglist *item = ast->siglist;
	int ret = 0;

	while (item) {
		if (call_reaver(item->sig, item->wanted)) {
			ret = -1;
			mail_storage_set_error(ctx->box->storage,
					       ME(NOTPOSSIBLE)
					       "Failed to call reaver");
			break;
		}
		item = item->next;
	}

	signature_list_free(&ast->siglist);
	i_free(ast);
	return ret;
}

static int backend_handle_mail(struct mailbox_transaction_context *t,
			       struct antispam_transaction_context *ast,
			       struct mail *mail, enum classification want)
{
	return signature_extract_to_list(t, mail, &ast->siglist, want);
}

static void backend_init(pool_t pool)
{
	const char *tmp;
	int i;

	tmp = get_setting("CRM_BINARY");
	if (tmp) {
		reaver_binary = tmp;
		debug("reaver binary set to %s\n", tmp);
	}

	tmp = get_setting("CRM_ARGS");
	if (tmp) {
		extra_args = p_strsplit(pool, tmp, ";");
		extra_args_num = str_array_length(
					(const char *const *)extra_args);
		for (i = 0; i < extra_args_num; i++)
			debug("reaver extra arg %s\n",
			      extra_args[i]);
	}

	signature_init();
}

static void backend_exit(void)
{
}

struct backend crm114_backend = {
	.init = backend_init,
	.exit = backend_exit,
	.handle_mail = backend_handle_mail,
	.start = backend_start,
	.rollback = backend_rollback,
	.commit = backend_commit,
};

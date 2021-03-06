/*
 * dspam backend for dovecot antispam plugin
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
#include <sys/types.h>
#include <sys/un.h>
#include <sys/socket.h>
#include <string.h>
#include <stdio.h>
#include <netinet/in.h>
#include <netdb.h>
#include "lib.h"
#include "mail-storage-private.h"

#include "antispam-plugin.h"
#include "tfsignature.h"

#define BUFSIZE 1024

static const char *tfdspam_binary = "/usr/bin/dspam";
static const char *tfdspam_result_header = NULL;
static uint16_t policyd_port = 7000;
static const char *policyd_address = "127.0.0.1";
static const char *policyd_socket_type = "unix";
static const char *policyd_socket_name = "/var/spool/postfix/private/policyd.sock";
static char **tfdspam_result_bl = NULL;
static int policyd_bool = 0;
static int tfdspam_result_bl_num = 0;
static char **tfextra_args = NULL;
static int tfextra_args_num = 0;

static int tfcall_dspam(const char *signature, enum classification wanted)
{
	pid_t pid;
	const char *class_arg;
	const char *sign_arg;
	int pipes[2];

	sign_arg = t_strconcat("--signature=", signature, NULL);
	switch (wanted) {
	case CLASS_NOTSPAM:
		class_arg = t_strconcat("--class=", "innocent", NULL);
		break;
	case CLASS_SPAM:
		class_arg = t_strconcat("--class=", "spam", NULL);
		break;
	}

	/*
	 * For dspam stderr; dspam seems to not always exit with a
	 * non-zero exit code on errors so we treat it as an error
	 * if it logged anything to stderr.
	 */
	if (pipe(pipes) < 0)
		return -1;

	pid = fork();
	if (pid < 0)
		return -1;

	if (pid) {
		int status;
		char buf[1025];
		int readsize;
		bool error = FALSE;

		close(pipes[1]);

		do {
			readsize = read(pipes[0], buf, sizeof(buf) - 1);
			if (readsize < 0) {
				readsize = -1;
				if (errno == EINTR)
					readsize = -2;
			}

			/*
			 * readsize > 0 means that we read a message from
			 * dspam, -1 means we failed to read for some odd
			 * reason
			 */
			if (readsize > 0 || readsize == -1)
				error = TRUE;

			if (readsize > 0) {
				buf[readsize] = '\0';
				debug("dspam error: %s\n", buf);
			}
		} while (readsize == -2 || readsize > 0);

		/*
		 * Wait for dspam, should return instantly since we've
		 * already waited above (waiting for stderr to close)
		 */
		waitpid(pid, &status, 0);
		if (!WIFEXITED(status))
			error = TRUE;

		close(pipes[0]);
		if (error)
			return 1;
		return WEXITSTATUS(status);
	} else {
		int fd = open("/dev/null", O_RDONLY);
		char **argv;
		/* 4 fixed args, extra args, terminating NULL */
		int sz = sizeof(char *) * (4 + tfextra_args_num + 1);
		int i;

		argv = i_malloc(sz);
		memset(argv, 0, sz);

		close(0);
		close(1);
		close(2);
		/* see above */
		close(pipes[0]);

		if (dup2(pipes[1], 2) != 2)
			exit(1);
		if (dup2(pipes[1], 1) != 1)
			exit(1);
		close(pipes[1]);

		if (dup2(fd, 0) != 0)
			exit(1);
		close(fd);

		argv[0] = (char *)tfdspam_binary;
		argv[1] = "--source=error";
		argv[2] = (char *)class_arg;
		argv[3] = (char *)sign_arg;

		for (i = 0; i < tfextra_args_num; i++)
			argv[i + 4] = (char *)tfextra_args[i];

		/*
		 * not good with stderr debuggin since we then write to
		 * stderr which our parent takes as a bug
		 */
		debugv_not_stderr(argv);

		execv(tfdspam_binary, argv);
		debug("executing %s failed: %d (uid=%d, gid=%d)",
			tfdspam_binary, errno, getuid(), getgid());
		/* fall through if dspam can't be found */
		exit(127);
		/* not reached */
		return -1;
	}
}

struct antispam_transaction_context {
	struct tfsiglist *siglist;
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
	tfsignature_list_free(&ast->siglist);
	i_free(ast);
}

static int backend_commit(struct mailbox_transaction_context *ctx,
			  struct antispam_transaction_context *ast)
{

	int sockfd;
	int error;
	socklen_t len = sizeof(error);
	size_t fstbracket, scndbracket, from_length;
	char str[4*BUFSIZE];
	char tmp[BUFSIZE];
	struct sockaddr_un serv_unix_addr;
	struct sockaddr_in serv_inet_addr;
	struct hostent *server;

	struct tfsiglist *item = ast->siglist;
	int ret = 0;

	if (policyd_bool == 1) {

		if (strcmp(policyd_socket_type, "unix") == 0) {

			sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
			if (sockfd < 0) {
				debug("ERROR opening policy unix socket. Function socket()");
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to create policyd socket");
				return -1;
			}

			serv_unix_addr.sun_family = AF_UNIX;
			strcpy(serv_unix_addr.sun_path, policyd_socket_name);

			if (connect(sockfd, (struct sockaddr *) &serv_unix_addr, sizeof(serv_unix_addr)) < 0) {
				getsockopt( sockfd, SOL_SOCKET, SO_ERROR, &error, &len);
				debug("Unix socket connection problem. Function connect(). Error: %s.", strerror(error));
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to connect to policyd.");
				return -1;
			}
		} else {

			sockfd = socket(AF_INET, SOCK_STREAM, 0);
			if (sockfd < 0) {
				debug("ERROR opening policy tcp socket. Function socket()");
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to create policyd socket.");
				return -1;
			}

			server = gethostbyname(policyd_address);
			if (server == NULL) {
				debug("ERROR, no such host. Function gethostbyname()");
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to get policyd host address");
				return -1;
			}

			memcpy(&serv_inet_addr.sin_addr, server->h_addr_list[0],server->h_length);

			serv_inet_addr.sin_port=htons(policyd_port);
			serv_inet_addr.sin_family=AF_INET;

			if(connect(sockfd,(struct sockaddr*)&serv_inet_addr,sizeof(serv_inet_addr)) < 0) {
				getsockopt( sockfd, SOL_SOCKET, SO_ERROR, &error, &len);
				debug("TCP socket connection problem. Function connect(). Error: %s.", strerror(error));
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to connect to policyd.");
				return -1;
			}
		}
	}

	while (item) {

		if (policyd_bool == 1) {
			memset(tmp, 0, BUFSIZE);
			memset(str, 0, 4*BUFSIZE);

			fstbracket = strcspn (item->from,"<") + 1;
			scndbracket = strcspn (item->from,">");

			from_length = strlen(item->from);

			if ((from_length + 1) == fstbracket || from_length == scndbracket) {
				fstbracket = 0;
				scndbracket = from_length;
			}

			if ((scndbracket - fstbracket - 1) > BUFSIZE) {
				debug("Too long 'from' field for tmp buffer with size %d", BUFSIZE);
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to create policyd request.");
				return -1;
			}

			strncpy(tmp, item->from+fstbracket, scndbracket - fstbracket);

			if ((strlen(tmp) + strlen(item->to) + 1 + 70) > 4*BUFSIZE) {
				//70 - size of sprintf template
				debug("Too long string for str buffer with size %d", 4*BUFSIZE);
				return -1;
			}

			sprintf(str, "request=junk_policy\nsender=%s\nrecipient=%s\nsasl_username=%s\naction=%s\n\n", item->to, tmp, item->to, ((item->wanted == 1) ? "spam": "notspam"));
			if (send(sockfd, str, strlen(str), 0) < 0) {
				debug("Socket send data problem. Function send()");
				mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to send request to policyd");
				return -1;
			}

		}
		if (item->sig_bool == 1) {
			if (tfcall_dspam(item->sig, item->wanted)) {
				ret = -1;
				mail_storage_set_error(ctx->box->storage,
							ME(NOTPOSSIBLE)
							"Failed to call dspam");
				break;
			}
		}
		item = item->next;
	}

	if (policyd_bool == 1) {
		if (close(sockfd) < 0) {
			debug("Failed to close policyd socket. Or we have problems with connection?");
			mail_storage_set_error(ctx->box->storage,
                                                        ME(NOTPOSSIBLE)
                                                        "Failed to close policyd socket.");
			ret = -1;
		}
	}

	tfsignature_list_free(&ast->siglist);
	i_free(ast);
	return ret;
}

static int backend_handle_mail(struct mailbox_transaction_context *t,
			       struct antispam_transaction_context *ast,
			       struct mail *mail, enum classification want)
{
	const char *const *result = NULL;
	int i;

	/*
	 * Check for whitelisted classifications that should
	 * be ignored when moving a mail. eg. virus.
	 */
	if (tfdspam_result_header)
		result = get_mail_headers(mail, tfdspam_result_header);
	if (result && result[0]) {
		for (i = 0; i < tfdspam_result_bl_num; i++) {
			if (strcasecmp(result[0], tfdspam_result_bl[i]) == 0)
				return 0;
		}
	}

	return tfsignature_extract_to_list(t, mail, &ast->siglist, want);
}

static void backend_init(pool_t pool)
{
	const char *tmp;
	int i;

	tmp = get_setting("POLICYD_ENABLE");
	if (tmp)
		policyd_bool = atoi(tmp);
	debug("policyd set to %d\n", policyd_bool);

	if (policyd_bool == 1) {
		tmp = get_setting("POLICYD_SOCKET_TYPE");
		if (tmp)
			policyd_socket_type = tmp;
		debug("policyd socket type set to %s\n", policyd_socket_type);

		if (strcmp(policyd_socket_type, "unix") == 0) {
			tmp = get_setting("POLICYD_SOCKET_NAME");
			if (tmp)
				policyd_socket_name = tmp;
			debug("policyd socket set to %s\n", policyd_socket_name);
		} else {
			if (strcmp(policyd_socket_type, "tcp") == 0) {
				tmp = get_setting("POLICYD_ADDRESS");
				if (tmp)
					policyd_address = tmp;
				debug("policyd address set to %s\n", policyd_address);
				tmp = get_setting("POLICYD_PORT");
				if (tmp)
					policyd_port = atoi(tmp);
				debug("policyd port set to %d\n", policyd_port);
			} else {
				policyd_bool = 0;
				debug("policyd set to %d\n", policyd_bool);
			}
		}
	}

	tmp = get_setting("DSPAM_BINARY");
	if (tmp)
		tfdspam_binary = tmp;
	debug("dspam binary set to %s\n", tfdspam_binary);

	tmp = get_setting("DSPAM_RESULT_HEADER");
	if (tmp) {
		tfdspam_result_header = tmp;
		debug("dspam result set to %s\n", tfdspam_result_header);

		tmp = get_setting("DSPAM_RESULT_BLACKLIST");
		if (tmp) {
			tfdspam_result_bl = p_strsplit(pool, tmp, ";");
			tfdspam_result_bl_num = str_array_length(
					(const char *const *)tfdspam_result_bl);
			for (i = 0; i < tfdspam_result_bl_num; i++)
				debug("dspam result blacklist %s\n",
						tfdspam_result_bl[i]);
		}
	}

	tmp = get_setting("DSPAM_ARGS");
	if (tmp) {
		tfextra_args = p_strsplit(pool, tmp, ";");
		tfextra_args_num = str_array_length(
					(const char *const *)tfextra_args);
		for (i = 0; i < tfextra_args_num; i++)
			debug("dspam extra arg %s\n",
			      tfextra_args[i]);
	}

	tfsignature_init();
}

static void backend_exit(void)
{
}

struct backend tfdspam_backend = {
	.init = backend_init,
	.exit = backend_exit,
	.handle_mail = backend_handle_mail,
	.start = backend_start,
	.rollback = backend_rollback,
	.commit = backend_commit,
};

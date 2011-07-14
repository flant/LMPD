#ifndef _ANTISPAM_PLUGIN_H
#define _ANTISPAM_PLUGIN_H

#include "lib.h"
#include "str.h"
#include "client.h"
#include "ostream.h"
#include "dict.h"
#include "imap-search.h"
#include "dovecot-version.h"
#include <stdlib.h>

#define __stringify_1(x)	#x
#define stringify(x)		__stringify_1(x)

#define __PLUGIN_FUNCTION(name, ioe) \
	name ## _plugin_ ## ioe
#define _PLUGIN_FUNCTION(name, ioe) \
	__PLUGIN_FUNCTION(name, ioe)
#define PLUGIN_FUNCTION(ioe)	\
	_PLUGIN_FUNCTION(PLUGINNAME, ioe)

extern uint32_t PLUGIN_FUNCTION(id);

struct antispam_transaction_context;

enum classification {
	CLASS_NOTSPAM,
	CLASS_SPAM,
};

struct backend {
	void (*init)(pool_t pool);
	void (*exit)(void);
	/*
	 * Handle mail; parameters are
	 *  - t: transaction context
	 *  - ast: transaction context from backend_start()
	 *  - mail: the message
	 *  - wanted: the wanted classification determined by the user
	 */
	int (*handle_mail)(struct mailbox_transaction_context *t,
			   struct antispam_transaction_context *ast,
			   struct mail *mail, enum classification wanted);
	struct antispam_transaction_context *(*start)(struct mailbox *box);
	void (*rollback)(struct antispam_transaction_context *ast);
	int (*commit)(struct mailbox_transaction_context *ctx,
		      struct antispam_transaction_context *ast);
};

/* the selected backend */
extern struct backend *backend;

/* possible backends */
extern struct backend crm114_backend;
extern struct backend dspam_backend;
extern struct backend pipe_backend;
extern struct backend signature_backend;
extern struct backend spool2dir_backend;

enum antispam_debug_target {
	ADT_NONE,
	ADT_STDERR,
	ADT_SYSLOG,
};

extern enum antispam_debug_target debug_target;
extern int verbose_debug;

void debug(const char *fmt, ...) __attribute__ ((format (printf, 1, 2)));
void debugv(char **args);
void debugv_not_stderr(char **args);
void debug_verbose(const char *fmt, ...) __attribute__ ((format (printf, 1, 2)));

void antispam_mail_storage_created(struct mail_storage *storage);
extern void (*antispam_next_hook_mail_storage_created)(struct mail_storage *storage);
bool mailbox_is_spam(struct mailbox *box);
bool mailbox_is_trash(struct mailbox *box);
bool mailbox_is_unsure(struct mailbox *box);
const char *get_setting(const char *name);
extern bool antispam_can_append_to_spam;
bool keyword_is_spam(const char *keyword);

extern bool need_keyword_hook;
extern bool need_folder_hook;

/*
 * Dovecot version compat code
 */
#if DOVECOT_VERSION <= DOVECOT_VERSION_CODE(1, 1, 0)
#define mailbox_get_storage(s)	mailbox_get_storage((struct mailbox *)s)
#define mailbox_get_name(s)	mailbox_get_name((struct mailbox *)s)
#endif

#if DOVECOT_VERSION_CODE(1, 1, 0) == DOVECOT_VERSION || DOVECOT_VERSION_CODE(1, 2, 0) == DOVECOT_VERSION
#define __attr_unused__		ATTR_UNUSED
#define ME(err)			MAIL_ERROR_ ##err,
#define PLUGIN_ID		uint32_t PLUGIN_FUNCTION(id) = 0
#define mempool_unref(x)	pool_unref(x)

static inline struct istream *get_mail_stream(struct mail *mail)
{
	struct istream *result;
	if (mail_get_stream(mail, NULL, NULL, &result) < 0)
		return NULL;
	return result;
}

static inline const char *const *
get_mail_headers(struct mail *mail, const char *hdr)
{
	const char *const *result;
	if (mail_get_headers(mail, hdr, &result) < 0)
		return NULL;
	return result;
}

static inline struct ostream *
o_stream_create_from_fd(int fd, pool_t pool ATTR_UNUSED)
{
	return o_stream_create_fd(fd, 0, TRUE);
}

#if DOVECOT_VERSION_CODE(1, 2, 0) == DOVECOT_VERSION
static inline struct dict *
string_dict_init(const char *uri, const char *username)
{
	const char *base_dir;

	base_dir = getenv("BASE_DIR");
	if (base_dir == NULL)
		base_dir = "/var/run/dovecot";
	return dict_init(uri, DICT_DATA_TYPE_STRING, username, base_dir);
}
#else /* 1.1 */
static inline struct dict *
string_dict_init(const char *uri, const char *username)
{
	return dict_init(uri, DICT_DATA_TYPE_STRING, username);
}
#endif
#elif DOVECOT_VERSION_CODE(1, 0, 0) == DOVECOT_VERSION
#define ME(err)
#define PLUGIN_ID
#define str_array_length(x)	strarray_length(x)
#define mempool_unref(x)	pool_unref(*(x))

static inline struct istream *get_mail_stream(struct mail *mail)
{
	return mail_get_stream(mail, NULL, NULL);
}

static inline const char *const *
get_mail_headers(struct mail *mail, const char *hdr)
{
	return mail_get_headers(mail, hdr);
}

static inline struct ostream *
o_stream_create_from_fd(int fd, pool_t pool)
{
	return o_stream_create_file(fd, pool, 0, TRUE);
}

static inline struct dict *
string_dict_init(const char *uri, const char *username)
{
	return dict_init(uri, username);
}
#else
#error "Building against this dovecot version is not supported"
#endif
        
#endif /* _ANTISPAM_PLUGIN_H */

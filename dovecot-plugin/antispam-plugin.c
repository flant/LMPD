/*
 * antispam plugin for dovecot
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
 *
 * based on the original framework http://www.dovecot.org/patches/1.0/copy_plugin.c
 *
 * Please see http://johannes.sipsolutions.net/wiki/Projects/dovecot-dspam-integration
 * for more information on this code.
 *
 * Install the plugin in the usual dovecot module location.
 */

#include <stdlib.h>
#include <ctype.h>

/* dovecot headers we need */
#include "lib.h"
#include "str.h"
#include "client.h"
#include "mail-storage-private.h"
#include "antispam-version.h"

/* defined by imap, pop3, lda */
extern void (*hook_mail_storage_created)(struct mail_storage *storage);

/* internal stuff we need */
#include "antispam-plugin.h"

/* macro since only needed for dovecot 1.1 */
PLUGIN_ID;

static pool_t global_pool;

static char *default_spam_folders[] = {
	"SPAM",
	NULL
};

enum match_type {
	MT_REG,
	MT_PATTERN,
	MT_PATTERN_IGNCASE,

	/* keep last */
	NUM_MT
};

/*
 * There are three different matches for each folder type
 *
 * type			usage
 * ----------------------------
 * MT_REG		plain strcmp()
 * MT_PATTERN		case sensitive match with possible wildcards
 * MT_PATTERN_IGNCASE	case insensitive match with possible wildcards
 */
static char **trash_folders[]  = { NULL,		NULL, NULL };
static char **spam_folders[]   = { default_spam_folders,NULL, NULL };
static char **unsure_folders[] = { NULL,		NULL, NULL };

void (*antispam_next_hook_mail_storage_created)(struct mail_storage *storage);
bool antispam_can_append_to_spam = FALSE;
static char **spam_keywords = NULL;

bool need_keyword_hook;
bool need_folder_hook;

struct backend *backend = NULL;

/* lower-case string, but keep modified UTF7 unchanged */
static void lowercase_string(const char *in, char *out)
{
	char ch;

	while ((ch = *out++ = i_tolower(*in++))) {
		/* lower case */
		if (ch == '&') {
			/* modified UTF7 -- find end of sequence ('-') */
			while ((ch = *out++ = *in++)) {
				if (ch == '-')
					break;
			}
		}
	}
}

static bool mailbox_patternmatch(const struct mailbox *box,
				 const struct mail_storage *storage,
				 const char *name,
				 bool lowercase)
{
	const char *boxname;
	char *lowerboxname;
	int len;
	int rc;

	if (storage && mailbox_get_storage(box) != storage)
		return FALSE;

	t_push();

	boxname = mailbox_get_name(box);
	if (lowercase) {
		lowerboxname = t_buffer_get(strlen(boxname) + 1);
		lowercase_string(boxname, lowerboxname);
		boxname = lowerboxname;
	}

	len = strlen(name);
	if (len && name[len - 1] == '*') {
		/* any wildcard */
		--len;
	} else {
		/* compare EOS too */
		++len;
	}

	rc = memcmp(name, boxname, len) == 0;

	t_pop();

	return rc;
}

static bool mailbox_patternmatch_case(const struct mailbox *box,
				      const struct mail_storage *storage,
				      const char *name)
{
	return mailbox_patternmatch(box, storage, name, FALSE);
}

static bool mailbox_patternmatch_icase(const struct mailbox *box,
				       const struct mail_storage *storage,
				       const char *name)
{
	return mailbox_patternmatch(box, storage, name, TRUE);
}

typedef bool (*match_fn_t)(const struct mailbox *, const struct mail_storage *,
			   const char *);

/* match information */
static const struct {
	const char *human, *suffix;
	match_fn_t fn;
} match_info[NUM_MT] = {
	[MT_REG]		= { .human  = "exact match",
				    .suffix = "",
				    .fn     = mailbox_equals, },
	[MT_PATTERN]		= { .human  = "wildcard match",
				    .suffix = "_PATTERN",
				    .fn     = mailbox_patternmatch_case, },
	[MT_PATTERN_IGNCASE]	= { .human  = "case-insensitive wildcard match",
				    .suffix = "_PATTERN_IGNORECASE",
				    .fn     = mailbox_patternmatch_icase, },
};

static bool mailbox_in_list(struct mailbox *box, char ***patterns)
{
	enum match_type i;
	char **list;

	if (!patterns)
		return FALSE;

	for (i = 0; i < NUM_MT; i++) {
		list = patterns[i];
		if (!list)
			continue;

		while (*list) {
			if (match_info[i].fn(box, box->storage, *list))
				return TRUE;
			list++;
		}
	}

	return FALSE;
}

bool mailbox_is_spam(struct mailbox *box)
{
	bool ret;

	ret = mailbox_in_list(box, spam_folders);
	debug_verbose("mailbox_is_spam(%s): %d\n", mailbox_get_name(box), ret);
	return ret;
}

bool mailbox_is_trash(struct mailbox *box)
{
	bool ret;

	ret = mailbox_in_list(box, trash_folders);
	debug_verbose("mailbox_is_trash(%s): %d\n", mailbox_get_name(box), ret);
	return ret;
}

bool mailbox_is_unsure(struct mailbox *box)
{
	bool ret;

	ret = mailbox_in_list(box, unsure_folders);
	debug_verbose("mailbox_is_unsure(%s): %d\n", mailbox_get_name(box), ret);
	return ret;
}

bool keyword_is_spam(const char *keyword)
{
	char **k = spam_keywords;

	if (!spam_keywords)
		return FALSE;

	while (*k) {
		if (strcmp(*k, keyword) == 0)
			return TRUE;
		k++;
	}

	return FALSE;
}

const char *get_setting(const char *name)
{
	const char *env;

	t_push();
	env = t_strconcat(t_str_ucase(stringify(PLUGINNAME)),
			  "_",
			  name,
			  NULL);
	env = getenv(env);
	t_pop();

	return env;
}

static int parse_folder_setting(const char *setting, char ***strings,
				const char *display_name)
{
	const char *tmp;
	int cnt = 0;
	enum match_type i;

	t_push();

	for (i = 0; i < NUM_MT; ++i) {
		tmp = get_setting(t_strconcat(setting, match_info[i].suffix,
				  NULL));
		if (tmp) {
			strings[i] = p_strsplit(global_pool, tmp, ";");
			if (i == MT_PATTERN_IGNCASE) {
				/* lower case the string */
				char **list = strings[i];
				while (*list) {
					lowercase_string(*list, *list);
					++list;
				}
			}
		}

		if (strings[i]) {
			char **iter = strings[i];
			while (*iter) {
				++cnt;
				debug("\"%s\" is %s %s folder\n", *iter,
					match_info[i].human, display_name);
				iter++;
			}
		}
	}

	t_pop();

	if (!cnt)
		debug("no %s folders\n", display_name);

	return cnt;
}

void PLUGIN_FUNCTION(init)(void)
{
	const char *tmp;
	char * const *iter;
	int spam_folder_count;

	debug_target = ADT_NONE;
	verbose_debug = 0;

	tmp = get_setting("DEBUG_TARGET");
	if (tmp) {
		if (strcmp(tmp, "syslog") == 0)
			debug_target = ADT_SYSLOG;
		else if (strcmp(tmp, "stderr") == 0)
			debug_target = ADT_STDERR;
		else
			exit(4);
	}

	debug("plugin initialising (%s)\n", ANTISPAM_VERSION);

	tmp = get_setting("VERBOSE_DEBUG");
	if (tmp) {
		char *endp;
		unsigned long val = strtoul(tmp, &endp, 10);
		if (*endp || val >= 2) {
			debug("Invalid verbose_debug setting");
			exit(5);
		}
		verbose_debug = val;
		debug_verbose("verbose debug enabled");
	}

	global_pool = pool_alloconly_create("antispam-pool", 1024);

	parse_folder_setting("TRASH", trash_folders, "trash");
	spam_folder_count = parse_folder_setting("SPAM", spam_folders, "spam");
	parse_folder_setting("UNSURE", unsure_folders, "unsure");

	tmp = get_setting("ALLOW_APPEND_TO_SPAM");
	if (tmp && strcasecmp(tmp, "yes") == 0) {
		antispam_can_append_to_spam = TRUE;
		debug("allowing APPEND to spam folders");
	}

	tmp = get_setting("SPAM_KEYWORDS");
	if (tmp)
		spam_keywords = p_strsplit(global_pool, tmp, ";");

	if (spam_keywords) {
		iter = spam_keywords;
		while (*iter) {
			debug("\"%s\" is spam keyword\n", *iter);
			iter++;
		}
	}

	tmp = get_setting("BACKEND");
	if (tmp) {
		if (strcmp(tmp, "crm114") == 0)
			backend = &crm114_backend;
		else if (strcmp(tmp, "dspam") == 0)
			backend = &dspam_backend;
                else if (strcmp(tmp, "tfdspam") == 0)
                        backend = &tfdspam_backend;
		else if (strcmp(tmp, "pipe") == 0)
			backend = &pipe_backend;
		else if (strcmp(tmp, "signature") == 0)
			backend = &signature_backend;
		else if (strcmp(tmp, "spool2dir") == 0)
			backend = &spool2dir_backend;
		else {
			debug("selected invalid backend!\n");
			exit(3);
		}
	} else {
		debug("no backend selected!\n");
		exit(2);
	}

	/* set spam_folders to empty to only allow keywords */
	need_folder_hook = spam_folder_count > 0;
	need_keyword_hook = !!spam_keywords;

	backend->init(global_pool);

	antispam_next_hook_mail_storage_created = hook_mail_storage_created;
	hook_mail_storage_created = antispam_mail_storage_created;
}

void PLUGIN_FUNCTION(deinit)(void)
{
	hook_mail_storage_created = antispam_next_hook_mail_storage_created;
	backend->exit();
	mempool_unref(&global_pool);
}

/* put dovecot version we built against into plugin for checking */
const char *PLUGIN_FUNCTION(version) = PACKAGE_VERSION;

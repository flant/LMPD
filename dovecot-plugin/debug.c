#define _BSD_SOURCE
#include <syslog.h>
#include <stdarg.h>
#include <stdio.h>
#include "antispam-plugin.h"

enum antispam_debug_target debug_target;
int verbose_debug;

static void _debug(const char *format, va_list ap)
{
	const char *fmt;

	if (debug_target == ADT_NONE)
		return;

	t_push();

	fmt = t_strconcat(stringify(PLUGINNAME), ": ", format, NULL);

	switch (debug_target) {
	case ADT_NONE:
		break;
	case ADT_SYSLOG:
		vsyslog(LOG_DEBUG, fmt, ap);
		break;
	case ADT_STDERR:
		vfprintf(stderr, fmt, ap);
		fflush(stderr);
		break;
	}

	t_pop();
}

void debug(const char *fmt, ...)
{
	va_list args;

	va_start(args, fmt);
	_debug(fmt, args);
	va_end(args);
}

void debugv(char **args)
{
	size_t len, pos = 0, buflen = 1024;
	char *buf;
	const char *str;

	t_push();
	buf = t_buffer_get(buflen);

	while (1) {
		str = *args;
		if (!str)
			break;
		len = strlen(str);
		if (pos + len + 1 >= buflen) {
			buflen = nearest_power(pos + len + 2);
			buf = t_buffer_reget(buf, buflen);
		}

		memcpy(buf + pos, str, len);
		pos += len;
		buf[pos++] = ' ';
		args++;
	}

	buf[pos++] = '\0';

	t_buffer_alloc(pos);

	debug("%s", buf);
	t_pop();
}

void debugv_not_stderr(char **args)
{
	if (debug_target == ADT_STDERR)
		return;

	debugv(args);
}

void debug_verbose(const char *fmt, ...)
{
	va_list args;

	if (!verbose_debug)
		return;

	va_start(args, fmt);
	_debug(fmt, args);
	va_end(args);
}

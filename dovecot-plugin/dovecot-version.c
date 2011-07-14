#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "config.h"

int main(int argc, char **argv)
{
	const char *v = PACKAGE_STRING;
	char *e;
	int maj = 0, min = 0, patch = 0;

	if (strncmp(v, "dovecot ", 8) && strncmp(v, "Dovecot ", 8))
		return 1;

	/* skip "dovecot " */
	v += 8;

	maj = strtol(v, &e, 10);
	if (v == e)
		return 1;

	v = e + 1;

	min = strtol(v, &e, 10);
	if (v == e)
		return 1;

	/* not end of string yet? */
	if (*e) {
		v = e + 1;

		patch = strtol(v, &e, 10);
		if (v == e)
			return 1;
	}

	printf("/* Auto-generated file, do not edit */\n\n");
	printf("#define DOVECOT_VERSION_CODE(maj, min, patch)	"
		"((maj)<<16 | ((min)<<8) | (patch))\n\n");
	
	printf("#define DOVECOT_VERSION				"
		"0x%.2x%.2x%.2x\n", maj, min, 0);
	printf("#define DOVECOT_VPATCH				"
		"0x%.2x%.2x%.2x\n", maj, min, patch);
	printf("#define ANTISPAM_STORAGE			"
		"\"antispam-storage-%d.%d.c\"\n", maj, min);

	return 0;
}

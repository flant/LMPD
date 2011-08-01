#!/bin/sh

VERSION=1.4

#if head=$(git rev-parse --verify HEAD 2>/dev/null); then
#	git update-index --refresh --unmerged > /dev/null
#	descr=$(git describe)
#
#	# on git builds check that the version number above
#	# is correct...
#	[ "${descr%%-*}" = "v$VERSION" ] || exit 2
#
#	echo -n '#define ANTISPAM_VERSION "'
#	echo -n "${descr#v}"
#	if git diff-index --name-only HEAD | read dummy ; then
#		echo -n "-dirty"
#	fi
#	echo '"'
#else
	echo '#define ANTISPAM_VERSION "'$VERSION'-notgit"'
#fi

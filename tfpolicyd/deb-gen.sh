#!/bin/sh

sudo apt-get -y install lsb-release gpgv

BUILDPATH=`pwd`

CODENAME=`lsb_release -a 2>/dev/null |grep "Codename:" | awk '{print $2}'`

sed -i "s/changeme/$CODENAME/g" $BUILDPATH/debian/changelog

dpkg-buildpackage -k860D255B

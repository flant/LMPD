#!/bin/sh

sudo apt-get -y install lsb-release gpg

BUILDPATH=`pwd`

CODENAME=`lsb_release -a 2>/dev/null |grep "Codename:" | awk '{print $2}'`

sed -i "s/changeme/$K/g" $BUILDPATH/debian/changelog

dpkg-buildpackage -k09B3B374

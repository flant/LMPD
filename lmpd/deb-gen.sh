#!/bin/bash

CHECKPKG=`dpkg --get-selections | egrep '^(gpgv|lsb-release)' | awk '{print $2}' | grep -v "deinstall" | wc -l`
if [ ! $CHECKPKG == "2" ]; then
sudo apt-get -y install lsb-release gpgv
else
echo "All needed packages installed"
fi

BUILDPATH=`pwd`

CODENAME=`lsb_release -a 2>/dev/null |grep "Codename:" | awk '{print $2}'`

sed -i "s/changeme/$CODENAME/g" $BUILDPATH/debian/changelog

dpkg-buildpackage -k860D255B $1

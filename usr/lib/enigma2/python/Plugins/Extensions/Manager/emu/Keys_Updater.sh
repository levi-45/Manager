#!/bin/sh
## DESCRIPTION=This script created by Levi45\nKeys Uodater
###############################################################################
SoftcamKeys="https://raw.githubusercontent.com/levi-45/Multicam/main/SoftCam.Key"
Constantcw="https://raw.githubusercontent.com/levi-45/Multicam/main/constant.cw"
OscamKeys="https://raw.githubusercontent.com/levi-45/Multicam/main/oscam.keys"
Oscamconstantcw="https://raw.githubusercontent.com/levi-45/Multicam/main/oscam.constant.cw"
echo ""
echo ""
echo "Downloading ${SoftcamKeys}"
wget ${SoftcamKeys} -O /usr/keys/SoftCam.Key || echo "Error: Couldn't connect to ${SoftcamKeys}"
echo ""
echo "Downloading ${SoftcamKeys}"
wget ${SoftcamKeys} -O /etc/tuxbox/config/SoftCam.Key || echo "Error: Couldn't connect to ${SoftcamKeys}"
echo ""
echo "Downloading ${Constantcw}"
wget ${Constantcw} -O /etc/tuxbox/config/constant.cw || echo "Error: Couldn't connect to ${Constantcw}"
echo ""
echo "Downloading ${Constantcw}"
wget ${Constantcw} -O /usr/keys/constant.cw || echo "Error: Couldn't connect to ${Constantcw}"
echo ""
echo "Downloading ${OscamKeys}"
wget ${OscamKeys} -O /etc/tuxbox/config/oscam.keys || echo "Error: Couldn't connect to ${OscamKeys}"
echo ""
echo "Downloading ${Oscamconstantcw}"
wget ${Oscamconstantcw} -O /etc/tuxbox/config/oscam.constant.cw || echo "Error: Couldn't connect to ${Oscamconstantcw}"
echo ""
echo ""
echo "#########################################################"
echo "#                           Levi45                      #"
echo "#########################################################"
echo "#              KEYS INSTALLED SUCCESSFULLY              #"
echo "#########################################################"
echo "#                    SATELLITE-FORUM.COM                #"
echo "#########################################################"
KeyDate=`/bin/date -r /usr/lib/enigma2/python/Plugins/Extensions/Manager/emu/Keys_Updater.sh +%d.%m.%y-%H:%M:%S`
	echo ""
	echo "UPDATE DATE AND TIME: $KeyDate"
exit 0

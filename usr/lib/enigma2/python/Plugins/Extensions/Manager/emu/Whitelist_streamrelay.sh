#!/bin/sh
##DESCRIPTION=Install Whitelist Streamrelay
[ ! -d "/etc/enigma2/whitelist_streamrelay" ] && wget -O /etc/enigma2/whitelist_streamrelay https://raw.githubusercontent.com/levi-45/Multicam/main/Arm/whitelist_streamrelay

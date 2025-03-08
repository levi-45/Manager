#!/bin/sh
##DESCRIPTION=Install *.ipk from /tmp
## Installin File
cd /tmp 
opkg install --force-overwrite --force-downgrade /tmp/*.ipk
rm -f *.ipk
cd ..

sync
echo "#########################################################"
echo "#                           Levi45                      #"
echo "#########################################################"
echo "#                 FILE INSTALLED SUCCESSFULLY           #"
echo "#########################################################"
echo "#                    SATELLITE-FORUM.COM                #"
echo "#########################################################"
exit 0

#!/bin/sh

## DESCRIPTION=This script created by Levi45\nActivity
echo "Activity.sh eseguito" > /tmp/activity_log.txt
top -n1 >> /tmp/activity_log.txt 2>&1

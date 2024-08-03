#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os
from os import environ as os_environ


global isDreamOS
isDreamOS = False
if os.path.exists("/var/lib/dpkg/status"):
    isDreamOS = True


MYFTP = 'aHR0cDovL2+xldmk0NS5zcGRu+cy5ldS9-BZGRv+bnMvTXVsdGljYW+0vYW-Rkb25z+Ln-htbA=='
plugin_path = '/usr/lib/enigma2/python/Plugins/Extensions/Manager/'
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2xldmktNDUvTWFuYWdlci9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9sZXZpLTQ1L01hbmFnZXI='
PluginLanguageDomain = 'Manager'
PluginLanguagePath = plugin_path + 'locale'


def wgetsts():
    wgetsts = False
    cmd22 = 'find /usr/bin -name "wget"'
    res = os.popen(cmd22).read()
    if 'wget' not in res.lower():
        if os.path.exists("/var/lib/dpkg/status"):
            cmd23 = 'apt-get update && apt-get install wget'
            os.popen(cmd23)
            wgetsts = True
        else:
            cmd23 = 'opkg update && opkg install wget'
            os.popen(cmd23)
            wgetsts = True
        return wgetsts


def localeInit():
    if os.path.isfile('/var/lib/dpkg/status'):
        lang = language.getLanguage()[:2]
        os_environ['LANGUAGE'] = lang
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


if os.path.isfile('/var/lib/dpkg/status'):
    _ = lambda txt: (gettext.dgettext(PluginLanguageDomain, txt) if txt else '')
    localeInit()
    language.addCallback(localeInit)
else:
    def _(txt):
        if gettext.dgettext(PluginLanguageDomain, txt):
            return gettext.dgettext(PluginLanguageDomain, txt)
        else:
            print('[' + PluginLanguageDomain + '] fallback to default translation for ' + txt)
            return gettext.gettext(txt)

    language.addCallback(localeInit)

#!/usr/bin/python
# -*- coding: utf-8 -*-

# -------------------#
#  coded by Lululla  #
#   skin by MMark    #
#     update to      #
#       Levi45       #
#     18/04/2024     #
#      No Coppy      #
# -------------------#
from . import _

from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eListboxPythonMultiContent
from enigma import gFont
from enigma import getDesktop
from os import listdir, mkdir
import os
import sys
import codecs

plugin_foo = os.path.dirname(sys.modules[__name__].__file__)
currversion = 'V.10.1-r33'
emu_script = str(plugin_foo) + '/emu'
name_plugemu = 'Levi45 Emu Keys %s' % currversion
screenwidth = getDesktop(0).size()

screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    skin_path = plugin_foo + '/res/skins/uhd/'
elif screenwidth.width() == 1920:
    skin_path = plugin_foo + '/res/skins/fhd/'
else:
    skin_path = plugin_foo + '/res/skins/hd/'

if os.path.exists("/var/lib/dpkg/status"):
    skin_path = skin_path + 'dreamOs/'
if not os.path.exists('/etc/clist.list'):
    with open('/etc/clist.list', 'w'):
        print('/etc/clist.list as been create')
        os.system('chmod 755 /etc/clist.list &')


def ulistEntry(download):
    res = [download]
    white = 16777215
    blue = 79488
    col = 16777215
    if screenwidth.width() == 2560:
        res.append(MultiContentEntryText(pos=(2, 0), size=(2000, 50), font=0, text=download, color=col, color_sel=white, backcolor_sel=blue))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryText(pos=(2, 0), size=(900, 40), font=0, text=download, color=col, color_sel=white, backcolor_sel=blue))
    else:
        res.append(MultiContentEntryText(pos=(2, 0), size=(660, 40), font=0, text=download, color=col, color_sel=white, backcolor_sel=blue))
    return res


def ulistx(data, list):
    icount = 0
    mlist = []
    for line in data:
        name = data[icount]
        mlist.append(ulistEntry(name))
        icount = icount + 1
    list.setList(mlist)


class M3UList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, False, eListboxPythonMultiContent)
        if screenwidth.width() == 2560:
            self.l.setItemHeight(50)
            textfont = int(44)
            self.l.setFont(0, gFont('Regular', textfont))
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(44)
            textfont = int(38)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(38)
            textfont = int(32)
            self.l.setFont(0, gFont('Regular', textfont))


class Levi45EmuKeysUpdater(Screen):

    def __init__(self, session, args=None):
        Screen.__init__(self, session)
        skin = os.path.join(skin_path, 'Levi45EmuKeysUpdater.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.session = session
        self.setTitle(name_plugemu)
        self['labstatus'] = Label(_('NO SCRIPT FOUND'))

        self.mlist = []
        self.populateScript()
        self['list'] = List(self.mlist)
        self['list'].onSelectionChanged.append(self.schanged)

        self['actions'] = ActionMap(['OkCancelActions'], {'ok': self.messagern, 'cancel': self.close}, -1)

        self.onLayoutFinish.append(self.script_sel)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(name_plugemu)

    def script_sel(self):
        self['list'].index = 1
        self['list'].index = 0

    def populateScript(self):
        try:
            if not os.path.exists('/usr/script'):
                mkdir('/usr/script', 493)
            if not os.path.exists(emu_script):
                mkdir(emu_script, 493)
        except:
            pass
        self.names = []
        self.urls = []
        myscripts = listdir(emu_script)
        for fil in myscripts:
            if fil.find('.sh') != -1:
                fil2 = fil[:-3].replace('_', ' ')  # .upper()
                desc = 'No Info Available'
                myfil = emu_script + '/' + fil
                print('myfil: ', myfil)
                # lululla fixed encode crash on atv py3
                with codecs.open(myfil, "rb", encoding="latin-1") as f:
                    for line in f.readlines():
                        if line.find('#DESCRIPTION=') != -1:
                            line = line.strip()
                            desc = line[13:]
                f.close()
                res = (fil2, desc)
                self.mlist.append(res)

    def messagern(self):
        self.session.openWithCallback(self.run, MessageBox, _('You want to send this command?'), MessageBox.TYPE_YESNO)

    def schanged(self):
        mysel = self['list'].getCurrent()
        if mysel:
            mytext = ' ' + mysel[1]
            self['labstatus'].setText(str(mytext))

    def run(self, result):
        if result:
            if len(self.mlist) >= 0:
                mysel = self['list'].getCurrent()
                if mysel:
                    mysel = mysel[0]
                    mysel = mysel.replace(' ', '_')
                    mysel2 = emu_script + '/' + mysel + '.sh'
                    from os import access, X_OK, chmod
                    if not access(mysel2, X_OK):
                        chmod(mysel2, 0o0755)
                    mytitle = 'Levi45 Script: ' + mysel
                    self.session.open(Console, title=mytitle, cmdlist=[mysel2])


def main2(session, **kwargs):
    session.open(Levi45EmuKeysUpdater)


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [('Levi45 Emu Keys Updater', main2, 'Levi45 Emu Keys Updater', None)]
    else:
        return []


def Plugins(**kwargs):
    list = []
    logoemu = 'logoemu.png'
    if not os.path.isfile('/var/lib/dpkg/status'):
        logoemu = plugin_foo + '/res/pics/logoemu.png'
    list.append(PluginDescriptor(name=_(name_plugemu), description='Emu Keys', where=PluginDescriptor.WHERE_PLUGINMENU, icon=logoemu, fnc=main2))
    list.append(PluginDescriptor(name=_(name_plugemu), description='Emu Keys', where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon=logoemu, fnc=main2))
    return list

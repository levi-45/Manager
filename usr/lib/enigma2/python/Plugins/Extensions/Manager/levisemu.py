#!/usr/bin/python
# -*- coding: utf-8 -*-

# -------------------#
#  coded by Lululla  #
#   skin by MMark    #
#     update to      #
#       Levi45       #
#     08/01/2025     #
#      No Coppy      #
# -------------------#
from . import _

from Components.ActionMap import ActionMap
from Components.Sources.List import List
# from Components.MenuList import MenuList
# from Components.MultiContent import MultiContentEntryText
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
# from enigma import eListboxPythonMultiContent
# from enigma import gFont
from enigma import getDesktop
from os import listdir, mkdir
import os
import sys
import codecs
from os import makedirs
from random import choice
from requests import get, exceptions


plugin_foo = os.path.dirname(sys.modules[__name__].__file__)
currversion = 'V.10.1-r36'
emu_script = str(plugin_foo) + '/emu'
name_plugemu = 'Levi45 Emu Keys %s' % currversion
fps = "https://patbuweb.com/script/script.tar"


AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"
]

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


class Levi45EmuKeysUpdater(Screen):

    skin = """
            <screen name="Levi45EmuKeysUpdater" position="center,center" size="1920,1080" Title="Acherone Script" backgroundColor="transparent" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Manager/res/pics/hd/mcmaneger.png" transparent="1" position="1613,711" size="190,193" alphatest="blend" zPosition="3" />
                <widget name="labstatus" position="1013,781" size="542,136" font="Regular; 26" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#202020" transparent="0" zPosition="5" />
                <!-- Menu List -->
                <widget source="list" render="Listbox" position="56,151" size="838,695" font="Regular;34" itemHeight="50" scrollbarMode="showOnDemand" transparent="1" zPosition="5" foregroundColor="#00a0a0a0" foregroundColorSelected="#ffffff" backgroundColor="#20000000" backgroundColorSelected="#0b2049">
                    <convert type="TemplatedMultiContent">
                        {"template": [
                            MultiContentEntryText(pos=(0, 0), size=(800, 50), font=0, flags=RT_HALIGN_LEFT, text=1),  # Nome script
                            <!-- MultiContentEntryText(pos=(300, 0), size=(500, 50), font=0, flags=RT_HALIGN_RIGHT, text=1),  # Descrizione -->
                        ],
                        "fonts": [gFont("Regular", 34)],
                        "itemHeight": 50}
                    </convert>
                </widget>
                <widget name="line1" position="134,34" size="776,80" font="Regular;42" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#202020" transparent="0" zPosition="1" />
                <widget font="Regular; 30" halign="right" position="1401,20" render="Label" size="500,40" source="global.CurrentTime" transparent="1">
                <convert type="ClockToText">Format:%a %d.%m. | %H:%M</convert>
                </widget>
                <eLabel backgroundColor="red" cornerRadius="3" position="34,1064" size="296,6" zPosition="11" />
                <eLabel backgroundColor="green" cornerRadius="3" position="342,1064" size="300,6" zPosition="11" />
                <eLabel backgroundColor="yellow" cornerRadius="3" position="652,1064" size="300,6" zPosition="11" />
                <eLabel backgroundColor="blue" cornerRadius="3" position="962,1064" size="300,6" zPosition="11" />
                <widget name="key_red" render="Label" position="32,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_green" render="Label" position="342,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_yellow" render="Label" position="652,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_blue" render="Label" position="962,1016" size="300,45" zPosition="11" font="Regular; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <eLabel backgroundColor="#002d3d5b" cornerRadius="20" position="0,0" size="1920,1080" zPosition="-99" />
                <eLabel backgroundColor="#001a2336" cornerRadius="30" position="20,1014" size="1880,60" zPosition="-80" />
                <eLabel name="" position="31,30" size="901,977" zPosition="-90" cornerRadius="18" backgroundColor="#00171a1c" foregroundColor="#00171a1c" />
                <widget source="session.VideoPicture" render="Pig" position="997,100" zPosition="19" size="880,499" backgroundColor="transparent" transparent="0" cornerRadius="14" />
            </screen>"""

    def __init__(self, session, args=None):
        Screen.__init__(self, session)
        skin = os.path.join(skin_path, 'Levi45EmuKeysUpdater.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.session = session
        self.setTitle(name_plugemu)
        self['labstatus'] = Label(_('NO SCRIPT FOUND'))
        self.mlist = []
        # self.populateScript()
        self['list'] = List(self.mlist)
        self['list'].onSelectionChanged.append(self.schanged)
        self['line1'] = Label(_('Available Scripts'))
        self['key_red'] = Label(_('Close'))
        self['key_green'] = Label(_('Select'))
        self['key_yellow'] = Label(_('Download'))
        self['key_blue'] = Label(_('Remove'))
        self["actions"] = ActionMap(['OkCancelActions', 'ColorActions'], {
            'ok': self.messagern,
            'green': self.messagern,
            'yellow': self.download,
            'blue': self.sremove,
            'cancel': self.close,
        }, -1)

        self.onShown.append(self.populateScript)
        self.onLayoutFinish.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(name_plugemu)

    def script_sel(self):
        self['list'].index = 1
        self['list'].index = 0

    def populateScript(self):
        try:
            if not os.path.exists('/usr/script'):
                makedirs('/usr/script', 493)

            if not os.path.exists(emu_script):
                mkdir(emu_script, 493)
        except:
            pass

        myscripts = listdir('/usr/script')
        scripts = []
        for fil in myscripts:
            if fil.endswith('.sh'):
                fil2 = fil[:-3]
                myfil = '/usr/script/' + str(fil)
                desc = None
                with codecs.open(myfil, "rb", encoding="latin-1") as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line.startswith('#DESCRIPTION='):
                            desc = line[13:]
                            break
                        elif line.startswith('##DESCRIPTION='):
                            desc = line[14:]
                            break

                if not desc:
                    desc = _("%s") % fil2
                desc = desc.replace('_', ' ').replace('-', ' ').capitalize()
                scripts.append((fil2, desc))

        scripts.sort(key=lambda x: x[0].lower())
        self.mlist = scripts
        self['list'].setList(self.mlist)

    def schanged(self):
        mysel = self['list'].getCurrent()
        if mysel:
            mytext = ' ' + mysel[1]
            self['labstatus'].setText(str(mytext))
        else:
            self["labstatus"].setText(_("Emu Script %s") % currversion)

    def messagern(self):
        if len(self.mlist) > 0:
            self.session.openWithCallback(self.run, MessageBox, _('You want to send this command?'), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _('Please Download Script!'), MessageBox.TYPE_INFO)

    def run(self, answer=False):
        if answer:
            if len(self.mlist) > 0:
                mysel = self['list'].getCurrent()
                if mysel:
                    mysel = mysel[0]
                    mysel2 = '/usr/script/' + mysel + '.sh'
                    from os import access, X_OK, chmod
                    if not access(mysel2, X_OK):
                        chmod(mysel2, 0o0777)
                    mytitle = _("Levi45 Script %s") % mysel
                    self.session.open(Console, title=mytitle, cmdlist=[mysel2])

    def getScrip(self, url):
        dest = '/tmp/script.tar'
        headers = {"User-Agent": choice(AGENTS)}
        try:
            response = get(url, headers=headers, timeout=(3.05, 6))
            response.raise_for_status()
            with open(dest, 'wb') as file:
                file.write(response.content)
            command = "tar -xvf /tmp/script.tar -C /usr/script"
            os.system(command)
            if os.path.exists(dest):
                os.remove(dest)
            self.populateScript()
            self.session.open(MessageBox, _('Scripts downloaded and extracted successfully!'), MessageBox.TYPE_INFO)
        except exceptions.RequestException as error:
            print("Error during script download:", str(error))
            self.session.open(MessageBox, _('Error during script download: %s') % str(error), MessageBox.TYPE_ERROR)
        except Exception as e:
            print("Error during script extraction:", str(e))
            self.session.open(MessageBox, _('Error during script extraction: %s') % str(e), MessageBox.TYPE_ERROR)

    def download(self):
        self.session.openWithCallback(self.callMyMsg, MessageBox, _('Download Script Pack?'), MessageBox.TYPE_YESNO)

    def callMyMsg(self, answer=False):
        if answer:
            self.getScrip(fps)

    def sremove(self):
        self.session.openWithCallback(self.xremove, MessageBox, _('Remove all scripts from folder?'), MessageBox.TYPE_YESNO)

    def xremove(self, answer=False):
        if answer:
            command = "rm -rf /usr/script/*"
            os.system(command)
            self.populateScript()
            self.session.open(MessageBox, _('Scripts successfully removed!'), MessageBox.TYPE_INFO)


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

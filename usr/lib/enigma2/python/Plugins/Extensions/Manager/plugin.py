#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# -------------------#
#  coded by Lululla  #
#   skin by MMark    #
#     update to      #
#       Levi45       #
#      20240725      #
#      No Coppy      #
# -------------------#
from __future__ import print_function
# local import
from . import _, MYFTP, wgetsts, installer_url, developer_url
from . import Utils
from .Utils import RequestAgent
from .data.GetEcmInfo import GetEcmInfo
from .Console import Console as lsConsole

# enigma lib import
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
# from Screens.Console import Console
from Screens.Standby import TryQuitMainloop
# from Tools.BoundFunction import boundFunction
from Tools.Directories import (fileExists, resolveFilename, SCOPE_PLUGINS)
from Tools.LoadPixmap import LoadPixmap
from enigma import (
    eTimer,
    getDesktop,
)
from os import (mkdir, chmod)
from time import sleep
from twisted.web.client import getPage
import codecs
import os
import sys
import time
import json
from datetime import datetime
from xml.dom import minidom

global active, skin_path, local
global _session, runningcam

active = False
_session = None

PY3 = sys.version_info.major >= 3
if PY3:
    unicode = str
    unichr = chr
    long = int
    PY3 = True

currversion = '10.1-r32'
title_plug = 'Satellite-Forum.Com V.%s' % currversion
title_emu = 'Levi45 Emu Keys V.%s' % currversion
name_plug = 'Levi45 Cam Manager'
name_plugemu = 'Levi45 Emu Keys'
plugin_foo = os.path.dirname(sys.modules[__name__].__file__)
keys = '/usr/keys'
camscript = '/usr/camscript'
data_path = os.path.join(plugin_foo, 'data')
FILE_XML = os.path.join(plugin_foo, 'Manager.xml')
ECM_INFO = '/tmp/ecm.info'
ereral = MYFTP.replace('+', '').replace('-', '')
FTPxx_XML = Utils.b64decoder(ereral)
local = True
ECM_INFO = '/tmp/ecm.info'
EMPTY_ECM_INFO = ('', '0', '0', '0')
old_ecm_time = time.time()
info = {}
ecm = ''
SOFTCAM = 0
CCCAMINFO = 1
OSCAMINFO = 2
AgentRequest = RequestAgent()
runningcam = None


try:
    wgetsts()
except:
    pass


def checkdir():
    keys = '/usr/keys'
    camscript = '/usr/camscript'
    if not os.path.exists(keys):
        mkdir('/usr/keys')
    if not os.path.exists(camscript):
        mkdir('/usr/camscript')


checkdir()
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


class Manager(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global _session, runningcam
        _session = session
        skin = os.path.join(skin_path, 'Manager.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.namelist = []
        self.softcamslist = []
        self.oldService = ''
        try:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        except:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
        self["NumberActions"] = NumberActionMap(["NumberActions"], {'0': self.keyNumberGlobal,
                                                                    '1': self.keyNumberGlobal,
                                                                    '2': self.keyNumberGlobal,
                                                                    '8': self.keyNumberGlobal},)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'EPGSelectActions',
                                     'HotkeyActions',
                                     'InfobarEPGActions',
                                     'MenuActions'], {'ok': self.action,
                                                      'cancel': self.close,
                                                      'menu': self.configtv,
                                                      'blue': self.openemu,
                                                      # 'blue': self.Blue,
                                                      'yellow': self.download,
                                                      'green': self.action,
                                                      # 'info': self.cccam,
                                                      'info': self.CfgInfo,
                                                      'red': self.stop}, -1)
        self.setTitle(_(title_plug))
        self['title'] = Label()
        self['key_green'] = Label(_('Start'))
        self['key_yellow'] = Label(_('Cam Download'))
        self['key_red'] = Label(_('Stop'))
        self['key_blue'] = Label(_('Script Executor'))
        self['description'] = Label(_('Scanning and retrieval list softcam ...'))
        self['info'] = Label()
        self['infocam'] = Label()
        self["infocam"].setText("Softcam")
        self["list"] = List([])
        self.curCam = None
        self.curCam = self.readCurrent()
        self.readScripts()
        self.BlueAction = 'SOFTCAM'
        runningcam = 'softcam'
        self.setBlueKey()
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.cgdesc)
        except:
            self.timer.callback.append(self.cgdesc)
        self.timer.start(300, 1)
        self.EcmInfoPollTimer = eTimer()
        try:
            self.EcmInfoPollTimer_conn = self.EcmInfoPollTimer.timeout.connect(self.setEcmInfo)
        except:
            self.EcmInfoPollTimer.callback.append(self.setEcmInfo)
        self.EcmInfoPollTimer.start(200)
        self.onShown.append(self.ecm)
        self.onShown.append(self.setBlueKey)
        self.onHide.append(self.stopEcmInfoPollTimer)

    def setBlueKey(self):
        global runningcam
        self.curCam = self.readCurrent()
        # self.BlueAction = 'SOFTCAM'
        self["infocam"].setText("Softcam")
        if self.curCam is not None:
            nim = str(self.curCam).lower()
            print('nim lower=', nim)

            if 'oscam' in str(self.curCam).lower():
                print('oscam in nim')
                runningcam = "oscam"
                self["infocam"].setText("OSCAMINFO")
                self.BlueAction = 'OSCAMINFO'
                if os.path.exists(data_path + "/OScamInfo.pyo") or os.path.exists(data_path + '/OScamInfo.pyc'):
                    print('existe OScamInfo')

            if 'cccam' in str(self.curCam).lower():
                runningcam = "cccam"
                self.BlueAction = 'CCCAMINFO'
                self["infocam"].setText("CCCAMINFO")
                if os.path.exists(data_path + '/CCcamInfo.pyo') or os.path.exists(data_path + '/CCcamInfo.pyc'):
                    print('existe CCcamInfo')

            if 'movicam' in str(self.curCam).lower():
                print('movicam in nim')
                runningcam = "movicam"
                self.BlueAction = 'MOVICAMINFO'
                self["infocam"].setText("MOVICAMINFO")
                if os.path.exists(data_path + "/OScamInfo.pyo") or os.path.exists(data_path + '/OScamInfo.pyc'):
                    print('existe movicamInfo')

            if 'ncam' in str(self.curCam).lower():
                runningcam = "ncam"
                self.BlueAction = 'NCAMINFO'
                self["infocam"].setText("NCAMINFO")
                print('ncam in nim')
                if os.path.exists(data_path + "/NcamInfo.pyo") or os.path.exists(data_path + '/NcamInfo.pyc'):
                    print('existe NcamInfo')

        print('[setBlueKey] self.curCam= 11 ', self.curCam)
        print('[setBlueKey] self.BlueAction= 11 ', self.BlueAction)
        print('[setBlueKey] runningcam= 11 ', runningcam)

    def ShowSoftcamCallback(self):
        pass

    def Blue(self):
        from Plugins.Extensions.Manager.levisemu import Levi45EmuKeysUpdater
        self.session.open(Levi45EmuKeysUpdater)

    def cccam(self):
        print('[cccam] self.BlueAction are:', self.BlueAction)

        if 'oscam' in str(self.curCam).lower():
            try:
                try:
                    from Screens.OScamInfo import OscamInfoMenu
                    print('[cccam] OScamInfo')
                    self.session.open(OscamInfoMenu)
                except ImportError:
                    from .data.OScamInfo import OscamInfoMenu
                    print('[cccam] OScamInfo')
                    self.session.open(OscamInfoMenu)
            except Exception as e:
                print('[cccam] OScamInfo e:', e)
                pass

        elif 'ccam' in str(self.curCam).lower():
            try:
                from Screens.CCcamInfo import CCcamInfoMain
                print('[cccam 12] CCcamInfo')
                self.session.open(CCcamInfoMain)
            except ImportError:
                from .data.CCcamInfo import CCcamInfoMain
                print('[cccam 2] CCcamInfo')
                self.session.open(CCcamInfoMain)

        elif 'ncam' in str(self.curCam).lower():
            try:
                try:
                    from Screens.NcamInfo import NcamInfoMenu
                    print('[cccam] NcamInfo')
                    self.session.open(NcamInfoMenu)
                except ImportError:
                    from .data.NcamInfo import NcamInfoMenu
                    print('[cccam] NcamInfo')
                    self.session.open(NcamInfoMenu)
            except Exception as e:
                print('[cccam] NcamInfo e:', e)
                pass

        elif 'movicam' in str(self.curCam).lower():
            try:
                try:
                    from Screens.OScamInfo import OscamInfoMenu
                    print('[cccam] MOVICAMINFO')
                    self.session.open(OscamInfoMenu)
                except ImportError:
                    from .data.OScamInfo import OscamInfoMenu
                    print('[cccam] MOVICAMINFO')
                    self.session.open(OscamInfoMenu)
            except Exception as e:
                print('[cccam] MOVICAMINFO e:', e)
                pass
        else:
            return

    def callbackx(self, call=None):
        print('call:', call)
        pass

    def openemu(self):
        from Plugins.Extensions.Manager.levisemu import Levi45EmuKeysUpdater
        self.session.open(Levi45EmuKeysUpdater)

    def keyNumberGlobal(self, number):
        print('pressed', number)
        if number == 0:
            # button blue + 0
            self.openemu()
        elif number == 1:
            # button info + 1
            self.CfgInfo()
        elif number == 2:
            # button 2
            self.cccam()
        elif number == 8:
            # button 8
            self.messagekd()
        else:
            return

    def setEcmInfo(self):
        try:
            self.ecminfo = GetEcmInfo()
            newEcmFound, ecmInfo = self.ecminfo.getEcm()
            if newEcmFound:
                self['info'].setText(''.join(ecmInfo))
            else:
                self.ecm()
        except Exception as e:
            print(e)

    def ecm(self):
        try:
            ecmf = ''
            if os.path.exists(ECM_INFO):
                try:
                    with open(ECM_INFO) as f:
                        self["info"].text = f.read()
                except IOError:
                    pass
            else:
                self['info'].setText(ecmf)
        except Exception as e:
            print('error ecm: ', e)

    def stopEcmInfoPollTimer(self):
        self.EcmInfoPollTimer.stop()

    def messagekd(self):
        self.session.openWithCallback(self.keysdownload, MessageBox, _('Update SoftcamKeys from google search?'), MessageBox.TYPE_YESNO)

    def keysdownload(self, result):
        if result:
            script = ('%s/auto.sh' % plugin_foo)
            from os import access, X_OK
            if not access(script, X_OK):
                chmod(script, 493)
            if os.path.exists('/usr/keys/SoftCam.Key'):
                os.system('rm -rf /usr/keys/SoftCam.Key')
            # import subprocess
            # # subprocess.check_output(['bash', script])
            # subprocess.Popen(script, shell=True, executable='/bin/bash')
            # self.session.open(MessageBox, _('SoftcamKeys Updated!'), MessageBox.TYPE_INFO, timeout=5)
            cmd = script
            title = _("Installing Softcam Keys\nPlease Wait...")
            self.session.open(lsConsole, _(title), [cmd], closeOnSuccess=False)

    def CfgInfo(self):
        self.session.open(InfoCfg)

    def configtv(self):
        from Plugins.Extensions.Manager.data.datas import levi_config
        self.session.open(levi_config)

    def cgdesc(self):
        if len(self.namelist) >= 1:
            self['description'].setText(_('Select a cam to run ...'))
        else:
            self['description'].setText(_('Install Cam first!!!'))
            self.updateList()

    def getcont(self):
        cont = "Your Config':\n"
        arc = ''
        arkFull = ''
        libsssl = ''
        python = os.popen('python -V').read().strip('\n\r')
        arcx = os.popen('uname -m').read().strip('\n\r')
        libs = os.popen('ls -l /usr/lib/libss*.*').read().strip('\n\r')
        if arcx:
            arc = arcx
            print('arc= ', arc)
        if self.arckget():
            print('arkget= ', arkFull)
            arkFull = self.arckget()
        if libs:
            libsssl = libs
        cont += ' ------------------------------------------ \n'
        cont += 'Cpu: %s\nArchitecture info: %s\nPython V.%s\nLibssl(oscam):\n%s' % (arc, arkFull, python, libsssl)
        cont += ' ------------------------------------------ \n'
        cont += 'Button Info for Other Info\n'
        return cont

    def arckget(self):
        zarcffll = 'by Lululla'
        try:
            if os.path.exists('/var/lib/dpkg/info'):
                zarcffll = os.popen('dpkg --print-architecture | grep -iE "arm|aarch64|mips|cortex|sh4|sh_4"').read().strip('\n\r')
            else:
                zarcffll = os.popen('opkg print-architecture | grep -iE "arm|aarch64|mips|cortex|h4|sh_4"').read().strip('\n\r')
            return str(zarcffll)
        except Exception as e:
            print("Error ", e)

    def updateList(self):
        poPup = self.getcont()
        _session.open(MessageBox, poPup, MessageBox.TYPE_INFO, timeout=10)

    def openTest(self):
        pass

    def download(self):
        self.session.open(GetipklistLv)
        self.onShown.append(self.readScripts)

    def getLastIndex(self):
        a = 0
        if len(self.namelist) >= 0:
            for x in self.namelist[0]:
                if x == self.curCam:
                    return a
                a += 1
                print('aa=', a)
        # else:
            # return -1
        # return -1

    def action(self):
        i = len(self.softcamslist)
        if i < 1:
            return
        try:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        except:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
        self.session.nav.stopService()
        self.last = self.getLastIndex()
        if self['list'].getCurrent():
            self.var = self['list'].getIndex()
            '''
            # self.var = self['list'].getSelectedIndex()
            # # self.var = self['list'].getSelectionIndex()
            print('self var=== ', self.var)
            '''
            cmdx = 'chmod 755 /usr/camscript/*.*'  # + self.softcamslist[self.var][0] + '.sh'
            os.system(cmdx)
            curCam = self.readCurrent()
            if self.last is not None:
                try:
                    foldcurr = '/usr/bin/' + str(curCam)
                    foldscrpt = '/usr/camscript/' + str(curCam) + '.sh'
                    os.chmod(foldcurr, 0o755)
                    os.chmod(foldscrpt, 0o755)
                except OSError:
                    pass

                if self.last == self.var:
                    self.cmd1 = '/usr/camscript/' + self.softcamslist[self.var][0] + '.sh' + ' cam_res &'
                    _session.open(MessageBox, _('Please wait..\nRESTART CAM'), MessageBox.TYPE_INFO, timeout=5)
                    os.system(self.cmd1)
                    sleep(1)
                else:
                    self.cmd1 = '/usr/camscript/' + self.softcamslist[self.last][0] + '.sh' + ' cam_down &'
                    _session.open(MessageBox, _('Please wait..\nSTOP & RESTART CAM'), MessageBox.TYPE_INFO, timeout=5)
                    os.system(self.cmd1)
                    sleep(1)
                    self.cmd1 = '/usr/camscript/' + self.softcamslist[self.var][0] + '.sh' + ' cam_up &'
                    os.system(self.cmd1)
            else:
                try:
                    self.cmd1 = '/usr/camscript/' + self.softcamslist[self.var][0] + '.sh' + ' cam_up &'
                    _session.open(MessageBox, _('Please wait..\nSTART UP CAM'), MessageBox.TYPE_INFO, timeout=5)
                    os.system(self.cmd1)
                    sleep(1)
                except:
                    self.close()
            if self.last != self.var:
                try:
                    self.curCam = self.softcamslist[self.var][0]
                    self.writeFile()
                except:
                    self.close()
        self.session.nav.playService(self.oldService)
        self.EcmInfoPollTimer.start(200)
        self.readScripts()

    def writeFile(self):
        if self.curCam != '' or self.curCam is not None:
            print('self.curCam= 2 ', self.curCam)
            if sys.version_info[0] == 3:
                clist = open('/etc/clist.list', 'w', encoding='UTF-8')
            else:
                clist = open('/etc/clist.list', 'w')
            os.system('chmod 755 /etc/clist.list &')
            clist.write(str(self.curCam))
            clist.close()

        if sys.version_info[0] == 3:
            stcam = open('/etc/startcam.sh', 'w', encoding='UTF-8')
        else:
            stcam = open('/etc/startcam.sh', 'w')
        stcam.write('#!/bin/sh\n' + self.cmd1)
        stcam.close()
        os.system('chmod 755 /etc/startcam.sh &')
        return

    def stop(self):
        i = len(self.softcamslist)
        if i < 1:
            return
        global runningcam
        try:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        except:
            self.oldService = self.session.nav.getCurrentlyPlayingServiceOrGroup()
        self.session.nav.stopService()
        if self.curCam != 'None' or self.curCam is not None:
            self.EcmInfoPollTimer.stop()
            self.last = self.getLastIndex()
            if self.last is not None:  # or self.curCam != 'no':
                self.cmd1 = '/usr/camscript/' + self.softcamslist[self.last][0] + '.sh' + ' cam_down &'
                os.system(self.cmd1)
                self.curCam = None
                self.writeFile()
                sleep(1)
                if os.path.exists(ECM_INFO):
                    os.remove(ECM_INFO)
                _session.open(MessageBox, _('Please wait..\nSTOP CAM'), MessageBox.TYPE_INFO, timeout=5)
                self['info'].setText('CAM STOPPED')
                self.BlueAction = 'SOFTCAM'
                runningcam = 'softcam'
                self.readScripts()
        self.session.nav.playService(self.oldService)

    def readScripts(self):
        try:
            scriptlist = []
            pliste = []
            self.index = 0
            s = 0
            pathscript = '/usr/camscript/'
            for root, dirs, files in os.walk(pathscript):
                for name in files:
                    scriptlist.append(name)
                    s += 1
            i = len(self.softcamslist)
            del self.softcamslist[0:i]
            png1 = LoadPixmap(cached=True,
                              path=resolveFilename(SCOPE_PLUGINS,
                                                   "Extensions/Manager/res/img/{}".format('actcam.png')))
            png2 = LoadPixmap(cached=True,
                              path=resolveFilename(SCOPE_PLUGINS,
                                                   "Extensions/Manager/res/img/{}".format('defcam.png')))
            if s >= 1:
                for lines in scriptlist:
                    dat = pathscript + lines
                    if sys.version_info[0] == 3:
                        sfile = open(dat, 'r', encoding='UTF-8')
                    else:
                        sfile = open(dat, 'r')
                    for line in sfile:
                        if line[0:3] == 'OSD':
                            nam = line[5:len(line) - 2]
                            print('We are in Manager and cam is type  = ', nam)
                            if self.curCam != 'None' or self.curCam is not None:
                                if nam == self.curCam:
                                    self.softcamslist.append((nam,  png1, '(Active)'))
                                    pliste.append((nam, '(Active)'))
                                else:
                                    self.softcamslist.append((nam, png2, ''))
                                    pliste.append((nam, ''))
                            else:
                                self.softcamslist.append(nam, png2, '')
                                pliste.append(nam, '')
                            self.index += 1
                sfile.close()
                self.softcamslist.sort(key=lambda i: i[2], reverse=True)
                pliste.sort(key=lambda i: i[1], reverse=True)
                self.namelist = pliste
                print('self.namelist:', self.namelist)
                self["list"].setList(self.softcamslist)
            self.setBlueKey()
        except Exception as e:
            print('error scriptlist: ', e)

    def readCurrent(self):
        currCam = None
        self.FilCurr = ''
        if fileExists('/etc/CurrentBhCamName'):
            self.FilCurr = '/etc/CurrentBhCamName'
        else:
            self.FilCurr = '/etc/clist.list'
        if os.stat(self.FilCurr).st_size > 0:
            try:
                if sys.version_info[0] == 3:
                    clist = open(self.FilCurr, 'r', encoding='UTF-8')
                else:
                    clist = open(self.FilCurr, 'r')
            except:
                return
            if clist is not None:
                for line in clist:
                    currCam = line
                clist.close()
        return currCam

    '''
    def autocam(self):
        current = None
        try:
            if sys.version_info[0] == 3:
                clist = open(self.FilCurr, 'r', encoding='UTF-8')
            else:
                clist = open(self.FilCurr, 'r')
            print('found list')
        except:
            return

        if clist is not None:
            for line in clist:
                current = line
            clist.close()
        print('current =', current)
        if os.path.isfile('/etc/autocam.txt') is False:
            if sys.version_info[0] == 3:
                alist = open('/etc/autocam.txt', 'w', encoding='UTF-8')
            else:
                alist = open('/etc/autocam.txt', 'w')
            alist.close()
        self.autoclean()
        if sys.version_info[0] == 3:
            alist = open('/etc/autocam.txt', 'a', encoding='UTF-8')
        else:
            alist = open('/etc/autocam.txt', 'a')
        alist.write(self.oldService.toString() + '\n')
        self.last = self.getLastIndex()
        alist.write(current + '\n')
        alist.close()
        _session.open(MessageBox, _('Autocam assigned to the current channel'), MessageBox.TYPE_INFO, timeout=5)
        return

    def autoclean(self):
        delemu = 'no'
        if os.path.isfile('/etc/autocam.txt') is False:
            return
        if sys.version_info[0] == 3:
            myfile = open('/etc/autocam.txt', 'r', encoding='UTF-8')
        else:
            myfile = open('/etc/autocam.txt', 'r')

        if sys.version_info[0] == 3:
            myfile2 = open('/etc/autocam2.txt', 'w', encoding='UTF-8')
        else:
            myfile2 = open('/etc/autocam2.txt', 'w')
        icount = 0
        for line in myfile.readlines():
            if line[:-1] == self.oldService.toString():
                delemu = 'yes'
                icount = icount + 1
                continue
            if delemu == 'yes':
                delemu = 'no'
                icount = icount + 1
                continue
            myfile2.write(line)
            icount = icount + 1
        myfile.close()
        myfile2.close()
        os.system('rm /etc/autocam.txt')
        os.system('cp /etc/autocam2.txt /etc/autocam.txt')
        '''

    def cancel(self):
        self.close()


class GetipklistLv(Screen):

    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'GetipklistLv.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.names = []
        self.names_1 = []
        self.list = []
        self['list'] = MenuList([])
        self.setTitle(_(title_plug))
        self['title'] = Label(_(title_plug))
        self['description'] = Label(_('Getting the list, please wait ...'))
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Load'))
        self['key_yellow'] = Button()
        self['key_blue'] = Button()
        self['key_green'].hide()
        if os.path.exists(FILE_XML):
            self['key_green'].show()
        self['key_yellow'].hide()
        self['key_blue'].hide()
        self.addon = 'emu'
        self.url = ''
        global local
        local = False
        self.icount = 0
        self.downloading = False
        self.xml = str(FTPxx_XML)
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/status'):
            self.timer_conn = self.timer.timeout.connect(self._gotPageLoad)
        else:
            self.timer.callback.append(self._gotPageLoad)
        self.timer.start(500, 1)
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions'], {'ok': self.okClicked, 'cancel': self.close, 'green': self.loadpage, 'red': self.close}, -1)
        self.onShown.append(self.pasx)

    def pasx(self):
        pass

    def loadpage(self):
        global local
        if os.path.exists(FILE_XML):
            self.lists = []
            del self.names[:]
            del self.list[:]
            self["list"].l.setList(self.list)
            with open(FILE_XML, 'r') as f:
                self.xml = f.read()
                local = True
            self._gotPageLoad()

    def downloadxmlpage(self):
        url = str(FTPxx_XML)
        if PY3:
            url = url.encode()
        getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

    def errorLoad(self, error):
        print(str(error))
        self['description'].setText(_('Try again later ...'))
        self.downloading = False

    def _gotPageLoad(self):
        global local
        if local is False:
            self.xml = Utils.checkGZIP(self.xml)
        self.list = []
        self.names = []
        try:
            if self.xml:
                self.xmlparse = minidom.parseString(self.xml)
                for plugins in self.xmlparse.getElementsByTagName('plugins'):
                    self.names.append(str(plugins.getAttribute('cont')))
                self["list"].l.setList(self.names)
                self['description'].setText(_('Please select ...'))
                self.downloading = True
        except:
            self['description'].setText(_('Error processing server addons data'))

    def okClicked(self):
        try:
            if self.downloading is True:
                selection = str(self['list'].getCurrent())
                self.session.open(GetipklistLv2, self.xmlparse, selection)
            else:
                self.close()
        except:
            return


class GetipklistLv2(Screen):
    def __init__(self, session, xmlparse, selection):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'GetipklistLv.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        self.xmlparse = xmlparse
        self.selection = selection
        self.list = []
        adlist = []
        for plugins in self.xmlparse.getElementsByTagName('plugins'):
            if str(plugins.getAttribute('cont')) == self.selection:
                for plugin in plugins.getElementsByTagName('plugin'):
                    adlist.append(str(plugin.getAttribute('name')))
                continue
        adlist.sort()
        self['list'] = MenuList(adlist)
        self.setTitle(_(title_plug))
        self['title'] = Label(_(title_plug))
        self['description'] = Label(_('Select and Install'))
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button('Remove')
        self['key_yellow'] = Button('Restart')
        self['key_blue'] = Button()
        # self['key_green'].hide()
        # self['key_yellow'].hide()
        self['key_blue'].hide()
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.message,
                                                                          'cancel': self.close,
                                                                          'green': self.remove,
                                                                          'yellow': self.restart,
                                                                          }, -1)
        self.onLayoutFinish.append(self.start)

    def start(self):
        pass

    def message(self):
        self.session.openWithCallback(self.selclicked, MessageBox, _('Do you install this plugin ?'), MessageBox.TYPE_YESNO)

    def selclicked(self, result):
        if result:
            try:
                selection_country = self['list'].getCurrent()
                for plugins in self.xmlparse.getElementsByTagName('plugins'):
                    if str(plugins.getAttribute('cont')) == self.selection:
                        for plugin in plugins.getElementsByTagName('plugin'):
                            if str(plugin.getAttribute('name')) == selection_country:
                                self.com = str(plugin.getElementsByTagName('url')[0].childNodes[0].data)
                                self.dom = str(plugin.getAttribute('name'))
                                # test lululla
                                self.com = self.com.replace('"', '')
                                if ".deb" in self.com:
                                    if not os.path.exists('/var/lib/dpkg/info'):
                                        self.session.open(MessageBox,
                                                          _('Unknow Image!'),
                                                          MessageBox.TYPE_INFO,
                                                          timeout=5)
                                        return
                                    n2 = self.com.find("_", 0)
                                    self.dom = self.com[:n2]

                                if ".ipk" in self.com:
                                    if os.path.exists('/var/lib/dpkg/info'):
                                        self.session.open(MessageBox,
                                                          _('Unknow Image!'),
                                                          MessageBox.TYPE_INFO,
                                                          timeout=5)
                                        return
                                    n2 = self.com.find("_", 0)
                                    self.dom = self.com[:n2]
                                elif ".zip" in self.com:
                                    self.dom = self.com
                                elif ".tar" in self.com or ".gz" in self.com or "bz2" in self.com:
                                    self.dom = self.com
                                print('self.prombt self.com: ', self.com)
                                self.prombt()
                            else:
                                print('Return from prompt ')
                                self['description'].setText('Select')
                            continue
            except Exception as e:
                print('error prompt ', e)
                self['description'].setText('Error')
                return

    def prombt(self):
        self.plug = self.com.split("/")[-1]
        dest = "/tmp"
        if not os.path.exists(dest):
            os.system('ln -sf  /var/volatile/tmp /tmp')
        self.folddest = '/tmp/' + self.plug
        cmd2 = ''
        if ".deb" in self.plug:
            cmd2 = "dpkg -i '/tmp/" + self.plug + "'"
        if ".ipk" in self.plug:
            cmd2 = "opkg install --force-reinstall --force-overwrite '/tmp/" + self.plug + "'"
        elif ".zip" in self.plug:
            cmd2 = "unzip -o -q '/tmp/" + self.plug + "' -d /"
        elif ".tar" in self.plug and "gz" in self.plug:
            cmd2 = "tar -xvf '/tmp/" + self.plug + "' -C /"
        elif ".bz2" in self.plug and "gz" in self.plug:
            cmd2 = "tar -xjvf '/tmp/" + self.plug + "' -C /"
        cmd = cmd2
        cmd00 = "wget --no-check-certificate -U '%s' -c '%s' -O '%s';%s > /dev/null" % (AgentRequest, str(self.com), self.folddest, cmd)
        print('cmd00:', cmd00)
        title = (_("Installing %s\nPlease Wait...") % self.dom)
        self.session.open(lsConsole, _(title), [cmd00], closeOnSuccess=False)

    def remove(self):
        self.session.openWithCallback(self.removenow,
                                      MessageBox,
                                      _("Do you want to remove?"),
                                      MessageBox.TYPE_YESNO)

    def removenow(self, answer=False):
        if answer:
            selection_country = self['list'].getCurrent()
            for plugins in self.xmlparse.getElementsByTagName('plugins'):
                if str(plugins.getAttribute('cont')) == self.selection:
                    for plugin in plugins.getElementsByTagName('plugin'):
                        if str(plugin.getAttribute('name')) == selection_country:
                            self.com = str(plugin.getElementsByTagName('url')[0].childNodes[0].data)
                            self.dom = str(plugin.getAttribute('name'))
                            # test lululla
                            self.com = self.com.replace('"', '')
                            cmd = ''

                            if ".deb" in self.com:
                                if not os.path.exists('/var/lib/dpkg/info'):
                                    self.session.open(MessageBox,
                                                      _('Unknow Image!'),
                                                      MessageBox.TYPE_INFO,
                                                      timeout=5)
                                    return
                                self.plug = self.com.split("/")[-1]
                                n2 = self.plug.find("_", 0)
                                self.dom = self.plug[:n2]
                                cmd = "dpkg -r " + self.dom  # + "'"
                                print('cmd deb remove:', cmd)
                            if ".ipk" in self.com:
                                if os.path.exists('/var/lib/dpkg/info'):
                                    self.session.open(MessageBox,
                                                      _('Unknow Image!'),
                                                      MessageBox.TYPE_INFO,
                                                      timeout=5)
                                    return
                                self.plug = self.com.split("/")[-1]
                                n2 = self.plug.find("_", 0)
                                self.dom = self.plug[:n2]
                                cmd = "opkg remove " + self.dom  # + "'"
                                print('cmd ipk remove:', cmd)

                            title = (_("Removing %s") % self.dom)
                            self.session.open(lsConsole, _(title), [cmd])

    def restart(self):
        self.session.openWithCallback(self.restartnow, MessageBox, _("Do you want to restart Gui Interface?"), MessageBox.TYPE_YESNO)

    def restartnow(self, answer=False):
        if answer:
            self.session.open(TryQuitMainloop, 3)


class InfoCfg(Screen):
    def __init__(self, session):
        self.session = session
        skin = os.path.join(skin_path, 'InfoCfg.xml')
        with codecs.open(skin, "r", encoding="utf-8") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.list = []
        self.setTitle(_(title_plug))
        self['list'] = Label()
        self['actions'] = ActionMap(['OkCancelActions',
                                     'ColorActions',
                                     'DirectionActions',
                                     'HotkeyActions',
                                     'InfobarEPGActions',
                                     'ChannelSelectBaseActions'], {'ok': self.close,
                                                                   'back': self.close,
                                                                   'cancel': self.close,
                                                                   'yellow': self.update_me,
                                                                   'green': self.update_dev,
                                                                   'yellow_long': self.update_dev,
                                                                   'info_long': self.update_dev,
                                                                   'infolong': self.update_dev,
                                                                   'showEventInfoPlugin': self.update_dev,
                                                                   'red': self.close}, -1)
        self["paypal"] = Label()
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Force Update'))
        self['key_yellow'] = Button(_('Update'))
        self['key_blue'] = Button()
        self['key_green'].hide()
        self['key_yellow'].hide()
        self['key_blue'].hide()

        self.Update = False
        self.timer = eTimer()
        if os.path.exists('/var/lib/dpkg/status'):
            self.timer_conn = self.timer.timeout.connect(self.check_vers)
        else:
            self.timer.callback.append(self.check_vers)
        self.timer.start(500, 1)
        self['title'] = Label(_(title_plug))
        self['description'] = Label(_('Path Configuration Folder'))
        self.onShown.append(self.updateList)

    def check_vers(self):
        remote_version = '0.0'
        remote_changelog = ''
        req = Utils.Request(Utils.b64decoder(installer_url), headers={'User-Agent': AgentRequest})
        page = Utils.urlopen(req).read()
        if PY3:
            data = page.decode("utf-8")
        else:
            data = page.encode("utf-8")
        if data:
            lines = data.split("\n")
            for line in lines:
                if line.startswith("version"):
                    remote_version = line.split("=")
                    remote_version = line.split("'")[1]
                if line.startswith("changelog"):
                    remote_changelog = line.split("=")
                    remote_changelog = line.split("'")[1]
                    break
        self.new_version = remote_version
        self.new_changelog = remote_changelog
        # if float(currversion) < float(remote_version):
        if currversion < remote_version:
            self.Update = True
            # self.new_version = remote_version
            # self.new_changelog = remote_changelog
            # updatestr = title_plug
            # cvrs = 'New version %s is available' % self.new_version
            # cvrt = 'Changelog: %s\n\nPress yellow button to start updating' % self.new_changelog
            # self['info'].setText(updatestr)
            # self['pth'].setText(cvrs)
            # self['pform'].setText(cvrt)
            self['key_yellow'].show()
            self.mbox = self.session.open(MessageBox, _('New version %s is available\n\nChangelog: %s\n\nPress yellow button to start updating') % (self.new_version, self.new_changelog), MessageBox.TYPE_INFO, timeout=5)
        self['key_green'].show()

    def update_me(self):
        if self.Update is True:
            self.session.openWithCallback(self.install_update, MessageBox, _("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") % (self.new_version, self.new_changelog), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _("Congrats! You already have the latest version..."),  MessageBox.TYPE_INFO, timeout=4)

    def update_dev(self):
        req = Utils.Request(Utils.b64decoder(developer_url), headers={'User-Agent': AgentRequest})
        page = Utils.urlopen(req).read()
        data = json.loads(page)
        remote_date = data['pushed_at']
        strp_remote_date = datetime.strptime(remote_date, '%Y-%m-%dT%H:%M:%SZ')
        remote_date = strp_remote_date.strftime('%Y-%m-%d')
        self.session.openWithCallback(self.install_update, MessageBox, _("Do you want to install update ( %s ) now?") % (remote_date), MessageBox.TYPE_YESNO)

    def install_update(self, answer=False):
        if answer:
            self.session.open(lsConsole, 'Upgrading...', cmdlist=('wget -q "--no-check-certificate" ' + Utils.b64decoder(installer_url) + ' -O - | /bin/sh'), finishedCallback=self.myCallback, closeOnSuccess=False)
        else:
            self.session.open(MessageBox, _("Update Aborted!"),  MessageBox.TYPE_INFO, timeout=3)

    def myCallback(self, result=None):
        print('result:', result)
        return

    def getcont(self):
        cont = " ---- Type Cam For Your Box--- \n"
        cont += "Config Softcam Manager(Oscam)':\n"
        cont += "Default folder:\n"
        cont += "etc/tuxbox/config\n"
        cont += ' ------------------------------------------ \n'
        cont += ' ---- Type Oscam For Your Box--- \n'
        arc = ''
        arkFull = ''
        libsssl = ''
        arcx = os.popen('uname -m').read().strip('\n\r')
        python = os.popen('python -V').read().strip('\n\r')
        libs = os.popen('ls -l /usr/lib/libss*.*').read().strip('\n\r')
        if arcx:
            arc = arcx
            print('arc= ', arc)
        if self.arckget():
            print('arkget= ', arkFull)
            arkFull = self.arckget()
        if libs:
            libsssl = libs
        cont += ' ------------------------------------------ \n'
        cont += 'Cpu: %s\nArchitecture info: %s\nPython V.%s\nLibssl(oscam):\n%s\n' % (arc, arkFull, python, libsssl)
        cont += ' ------------------------------------------ \n'
        return cont

    def updateList(self):
        self["list"].setText(self.getcont())

    def arckget(self):
        zarcffll = 'by Lululla'
        try:
            if os.path.exists('/var/lib/dpkg/info'):
                zarcffll = os.popen('dpkg --print-architecture | grep -iE "arm|aarch64|mips|cortex|sh4|sh_4"').read().strip('\n\r')
            else:
                zarcffll = os.popen('opkg print-architecture | grep -iE "arm|aarch64|mips|cortex|h4|sh_4"').read().strip('\n\r')
            return str(zarcffll)
        except Exception as e:
            print("Error ", e)

    def Down(self):
        self['list'].pageDown()

    def Up(self):
        self['list'].pageUp()


def startConfig(session, **kwargs):
    session.open(Manager)


def mainmenu(menu_id):
    if menu_id == "setup":
        return [(_("Levi45 Softcam Manager"),
                 startConfig,
                 "Levi45 Softcam Manager",
                 50)]
    else:
        return []


def autostart(reason, session=None, **kwargs):
    """called with reason=1 to during shutdown, with reason=0 at startup?"""
    print('[Softcam] Started')
    if reason == 0:
        print('reason 0')
        if session is not None:
            print('session none')
            try:
                print('ok started autostart')
                if fileExists('/etc/init.d/dccamd'):
                    os.system('mv /etc/init.d/dccamd /etc/init.d/dccamdOrig &')
                if fileExists('/usr/bin/dccamd'):
                    os.system("mv /usr/bin/dccamd /usr/bin/dccamdOrig &")
                os.system('ln -sf /usr/bin /var/bin')
                os.system('ln -sf /usr/keys /var/keys')
                os.system('ln -sf /usr/scce /var/scce')
                # os.system('ln -sf /usr/camscript /var/camscript')
                os.system('sleep 2')
                os.system('/etc/startcam.sh &')
                os.system('sleep 2')
            except:
                print('except autostart')
        else:
            print('pass autostart')
    return


def menu(menu_id, **kwargs):
    print('here menu plugin')
    return [(name_plug, main, 'Levi45 Softcam Manager', 44)] if menu_id == "cam" else []


def main(session, **kwargs):
    try:
        session.open(Manager)
    except:
        pass


def main2(session, **kwargs):
    from . import levisemu
    session.open(levisemu.Levi45EmuKeysUpdater)


def menuemu(menu_id):
    if menu_id == 'mainmenu':
        return [(name_plugemu, main2, 'Levi45 Emu Keys Updater', 45)]
    else:
        return []


def StartSetup(menu_id):
    if menu_id == 'mainmenu':
        return [(name_plug, main, 'Levi45 Softcam Manager', 44)]
    else:
        return []


# fixed issue Lulu
logo = 'logo.png'
logoemu = 'logoemu.png'
if screenwidth.width() == 1920:
    logo = plugin_foo + '/res/pics/logo.png'
    logoemu = plugin_foo + '/res/pics/logoemu.png'


# plugin
mainDescriptor = PluginDescriptor(name=_(name_plug), where=[PluginDescriptor.WHERE_MENU], fnc=mainmenu)
extDescriptor = PluginDescriptor(name=_(name_plug), description=_(title_plug), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], icon=logo, fnc=main)
plugDescriptor = PluginDescriptor(name=_(name_plug), description=_(title_plug), where=[PluginDescriptor.WHERE_PLUGINMENU], icon=logo, fnc=main)
menuDescriptor = PluginDescriptor(name=_(name_plug), description=_(title_plug), where=[PluginDescriptor.WHERE_MENU], icon=logo, fnc=StartSetup)
startDescriptor = PluginDescriptor(name=_(name_plug), description=_(title_plug), where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], needsRestart=True, fnc=autostart)


# emu
mainemuDescriptor = PluginDescriptor(name=_(name_plugemu), description=_(title_emu), where=[PluginDescriptor.WHERE_MENU], icon=logoemu, fnc=menuemu)
plugemuDescriptor = PluginDescriptor(name=_(name_plugemu), description=_(title_emu), where=[PluginDescriptor.WHERE_PLUGINMENU], icon=logoemu, fnc=main2)
extemuDescriptor = PluginDescriptor(name=_(name_plugemu), description=_(title_emu), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], icon=logoemu, fnc=main2)


def Plugins(**kwargs):
    result = []
    result.append(mainDescriptor)
    result.append(extDescriptor)
    result.append(plugDescriptor)
    result.append(startDescriptor)
    result.append(menuDescriptor)
    return result

# -*- coding: UTF-8 -*-
# CCcam Info by AliAbdul
# Update CCcam Info By RAED Full HD Skin (1920x1080) 29-06-2015
# Update CCcam Info Dimitrij openPLi 19-04-2016
# Update from Lululla py3 and minor fix
# Update CCcam Info WanWizard openPLi 27-19-2023

from __future__ import print_function

from . import CCcamPrioMaker
from . import CCcamOrganizer

from Components.ActionMap import (
    ActionMap,
    NumberActionMap,
)
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (MultiContentEntryText, MultiContentEntryPixmapAlphaTest)
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import (
    config,
    ConfigSubsection,
    ConfigSelection,
    ConfigText,
    ConfigInteger,
    ConfigYesNo,
    getConfigListEntry,
)
from Plugins.Plugin import PluginDescriptor
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import InfoBar
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import (
    fileExists,
)

from base64 import encodebytes
from enigma import (
    eListboxPythonMultiContent,
    gFont,
    loadPNG,
    getDesktop,
    RT_HALIGN_RIGHT,
    ePoint,
    eTimer,
    iPlayableService,
    iServiceInformation,
    eSize,
)
from os import listdir, remove, rename, system
from skin import parseColor
from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory
import sys


if fileExists("/usr/lib/enigma2/python/Components/Console.pyc"):
    from Components.Console import Console
    NEW_CVS = True
else:
    from os import popen
    NEW_CVS = False

PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.parse import urlparse, urlunparse
else:
    from urlparse import urlparse, urlunparse


VERSION = "v1.6b"
DATE = "27.12.2023"
plugin_path = '/usr/lib/enigma2/python/Plugins/Extensions/CCcamInfo'
CFG = "/etc/CCcam.cfg"
ecmInfoStart = None
desktop = getDesktop(0)
size = desktop.size()
width = size.width()
lock_on = loadPNG(plugin_path + "/icons/lock_on.png")
lock_off = loadPNG(plugin_path + "/icons/lock_off.png")
TOGGLE_SHOW = InfoBar.toggleShow
# png = plugin_path + "/icons/key_%s.png" % str(idx)  #remember
# png = plugin_path + "/icons/key_%s.png" % color  #remember


def _parse(url):
    url = url.strip()
    parsed = urlparse(url)
    scheme = parsed.scheme
    host = parsed.hostname
    port = parsed.port or (443 if scheme == 'https' else 80)
    path = urlunparse(('', '') + parsed[2:])

    if '@' in host:
        username, host = host.split('@')
        if ':' in username:
            username, password = username.split(':')
        else:
            password = ""
    else:
        username = ""
        password = ""

    if ':' in host:
        host, port = host.split(':')
        port = int(port)

    if path == "":
        path = "/"

    return scheme, host, port, path, username, password


def getPage(url, contextFactory=None, *args, **kwargs):
    scheme, host, port, path, username, password = _parse(url)

    if username and password:
        url = scheme + '://' + host + ':' + str(port) + path
        basicAuth = encodebytes("%s:%s" % (username, password))
        authHeader = "Basic " + basicAuth.strip()
        AuthHeaders = {"Authorization": authHeader}
        if "headers" in kwargs:
            # if kwargs.has_key("headers"):
            kwargs["headers"].update(AuthHeaders)
        else:
            kwargs["headers"] = AuthHeaders

    factory = HTTPClientFactory(url.encode('utf-8'), *args, **kwargs)
    reactor.connectTCP(host, port, factory)

    return factory.deferred


class HelpableNumberActionMap(NumberActionMap):
    def __init__(self, parent, context, actions, prio):
        alist = []
        adict = {}
        for (action, funchelp) in actions.items():
            alist.append((action, funchelp[1]))
            adict[action] = funchelp[0]
        NumberActionMap.__init__(self, [context], adict, prio)
        parent.helpList.append((self, context, alist))


TranslationHelper = [
    ["Current time", _("Current time")],
    ["NodeID", _("NodeID")],
    ["Uptime", _("Uptime")],
    ["Connected clients", _("Connected clients")],
    ["Active clients", _("Active clients")],
    ["Total handled client ecm's", _("Total handled client ecm's")],
    ["Total handled client emm's", _("Total handled client emm's")],
    ["Peak load (max queued requests per workerthread)", _("Peak load (max queued requests per workerthread)")],
    ["card reader", _("card reader")],
    ["no or unknown card inserted", _("no or unknown card inserted")],
    ["system:", _("system:")],
    ["caid:", _("caid:")],
    ["provider:", _("provider:")],
    ["provid:", _("provid:")],
    ["using:", _("using:")],
    ["address:", _("address:")],
    ["hops:", _("hops:")],
    ["pid:", _("pid:")],
    ["share:", _("share:")],
    ["handled", _("handled")],
    [" and", _(" and")],
    ["card", _("card")],
    ["Cardserial", _("Cardserial")],
    ["ecm time:", _("ecm time:")]]


def translateBlock(block):
    for x in TranslationHelper:
        if block.__contains__(x[0]):
            block = block.replace(x[0], x[1])
    return block


def getConfigValue(lx):
    list = lx.split(":")
    ret = ""

    if len(list) > 1:
        ret = (list[1]).replace("\n", "").replace("\r", "")
        if ret.__contains__("#"):
            idx = ret.index("#")
            ret = ret[:idx]
        while ret.startswith(" "):
            ret = ret[1:]
        while ret.endswith(" "):
            ret = ret[:-1]

    return ret


def notBlackListed(entry):
    try:
        f = open(config.plugins.CCcamInfo.blacklist.value, "r")
        content = f.read().split("\n")
        f.close()
    except:
        content = []
    ret = True
    for x in content:
        if x == entry:
            ret = False
    return ret


menu_list = [
    _("General"),
    _("Clients"),
    _("Active clients"),
    _("Servers"),
    _("Shares"),
    _("Share View"),
    _("Extended Shares"),
    _("Providers"),
    _("Entitlements"),
    _("ecm.info"),
    _("Menu config"),
    _("Local box"),
    _("Remote box"),
    _("CCcam Prio Maker"),
    _("CCcam Organizer"),
    _("Switch config"),
    _("About")]


config.plugins.CCcamInfo = ConfigSubsection()
config.plugins.CCcamInfo.name = ConfigText(default="Profile", fixed_size=False)
config.plugins.CCcamInfo.ip = ConfigText(default="192.168.1.24", fixed_size=False)
config.plugins.CCcamInfo.username = ConfigText(default="", fixed_size=False)
config.plugins.CCcamInfo.password = ConfigText(default="", fixed_size=False)
config.plugins.CCcamInfo.port = ConfigInteger(default=16001, limits=(1, 65535))
config.plugins.CCcamInfo.profile = ConfigText(default="", fixed_size=False)
config.plugins.CCcamInfo.ecmInfoEnabled = ConfigYesNo(default=True)
config.plugins.CCcamInfo.ecmInfoMainMenu = ConfigYesNo(default=True)
config.plugins.CCcamInfo.showExtMenu = ConfigYesNo(default=True)
config.plugins.CCcamInfo.ecmInfoTime = ConfigInteger(default=5, limits=(1, 60))
config.plugins.CCcamInfo.ecmInfoForceHide = ConfigYesNo(default=True)
config.plugins.CCcamInfo.serverNameLength = ConfigInteger(default=22, limits=(10, 100))
config.plugins.CCcamInfo.ecmInfoPositionX = ConfigInteger(default=50)
config.plugins.CCcamInfo.ecmInfoPositionY = ConfigInteger(default=50)
config.plugins.CCcamInfo.show_cryptoinfo = ConfigYesNo(default=True)
config.plugins.CCcamInfo.ecmInfoPositionZ = ConfigSelection([(str(x), str(x)) for x in range(-20, 21)], "10")
config.plugins.CCcamInfo.blacklist = ConfigText(default="/etc/enigma2/CCcamInfo.blacklisted", fixed_size=False)
config.plugins.CCcamInfo.profiles = ConfigText(default="/etc/enigma2/CCcamInfo.profiles", fixed_size=False)


def getConfigNameAndContent(fileName):
    try:
        f = open(fileName, "r")
        content = f.read()
        f.close()
    except:
        content = ""

    if content.startswith("#CONFIGFILE NAME="):
        content = content.replace("\r", "\n")
        name = content[17:]
        idx = name.index("\n")
        name = name[:idx]
    else:
        name = fileName.replace("/etc/", "")

    return (name, content)


if width > 1280:
    MAX_X = 400
    MAX_Y = 62
    ORIGMAX_X = 1920
    ECMINFO_SKIN_NEW = """
        <screen position="0,0" size="1920,62" flags="wfNoBorder" zPosition="%s">
            <widget name="irdeto" position="0,0" size="30,30" font="Regular; 30" text="I" valign="center" halign="center" transparent="1" />
            <widget name="seca" position="30,0" size="30,30" font="Regular; 30" text="S" valign="center" halign="center" transparent="1" />
            <widget name="nagra" position="60,0" size="30,30" font="Regular; 30" text="N" valign="center" halign="center" transparent="1" />
            <widget name="via" position="90,0" size="30,30" font="Regular; 30" text="V" valign="center" halign="center" transparent="1" />
            <widget name="conax" position="120,0" size="45,30" font="Regular; 30" text="CO" valign="center" halign="center" transparent="1" />
            <widget name="betacrypt" position="165,0" size="40,31" font="Regular; 30" text="BC" valign="center" halign="center" transparent="1" />
            <widget name="crypto" position="207,0" size="45,30" font="Regular; 30" text="CW" valign="center" halign="center" transparent="1" />
            <widget name="dreamcrypt" position="253,0" size="45,30" font="Regular; 30" text="DC" valign="center" halign="center" transparent="1" />
            <widget name="nds" position="300,0" size="90,30" font="Regular; 30" text="NDS" valign="center" halign="center" transparent="1" />

            <widget name="drecrypt" position="0,32" size="30,30" font="Regular; 30" text="D" valign="center" halign="center" transparent="1" />
            <widget name="powervu" position="30,32" size="30,30" font="Regular; 30" text="P" valign="center" halign="center" transparent="1" />
            <widget name="verimatrix" position="60,32" size="60,30" font="Regular; 30" text="VM" valign="center" halign="center" transparent="1" />
            <widget name="rosscrypt" position="120,32" size="30,30" font="Regular; 30" text="R" valign="center" halign="center" transparent="1" />
            <widget name="exset" position="152,32" size="45,30" font="Regular; 30" text="ES" valign="center" halign="center" transparent="1" />
            <widget name="codicrypt" position="200,32" size="45,30" font="Regular; 30" text="C" valign="center" halign="center" transparent="1" />
            <widget name="digicipher" position="247,32" size="45,30" font="Regular; 30" text="DI" valign="center" halign="center" transparent="1" />
            <widget name="biss" position="295,32" size="100,30" font="Regular; 30" text="BISS" valign="center" halign="center" transparent="1" />

            <widget name="ecmInfo" position="400,15" size="1500,37" font="Regular; 35" valign="center" transparent="1" noWrap="1" />
        </screen>""" % config.plugins.CCcamInfo.ecmInfoPositionZ.value
else:
    MAX_X = 230
    MAX_Y = 34
    ORIGMAX_X = width
    ECMINFO_SKIN_NEW = """
        <screen position="0,0" size="%d,34" flags="wfNoBorder" zPosition="%s" >
            <widget name="irdeto" position="0,0" size="15,17" font="Regular;16" text="I" valign="center" halign="center" transparent="1" />
            <widget name="seca" position="15,0" size="15,17" font="Regular;16" text="S" valign="center" halign="center" transparent="1" />
            <widget name="nagra" position="30,0" size="15,17" font="Regular;16" text="N" valign="center" halign="center" transparent="1" />
            <widget name="via" position="45,0" size="15,17" font="Regular;16" text="V" valign="center" halign="center" transparent="1" />
            <widget name="conax" position="60,0" size="30,17" font="Regular;16" text="CO" valign="center" halign="center" transparent="1" />
            <widget name="betacrypt" position="90,0" size="25,17" font="Regular;16" text="BC" valign="center" halign="center" transparent="1" />
            <widget name="crypto" position="112,0" size="35,17" font="Regular;16" text="CW" valign="center" halign="center" transparent="1" />
            <widget name="dreamcrypt" position="147,0" size="25,17" font="Regular;16" text="DC" valign="center" halign="center" transparent="1" />
            <widget name="nds" position="172,0" size="45,17" font="Regular;16" text="NDS" valign="center" halign="center" transparent="1" />

            <widget name="drecrypt" position="0,16" size="15,17" font="Regular;16" text="D" valign="center" halign="center" transparent="1" />
            <widget name="powervu" position="17,16" size="15,17" font="Regular;16" text="P" valign="center" halign="center" transparent="1" />
            <widget name="verimatrix" position="34,16" size="30,17" font="Regular;16" text="VM" valign="center" halign="center" transparent="1" />
            <widget name="rosscrypt" position="66,16" size="15,17" font="Regular;16" text="R" valign="center" halign="center" transparent="1" />
            <widget name="exset" position="83,16" size="30,17" font="Regular;16" text="ES" valign="center" halign="center" transparent="1" />
            <widget name="codicrypt" position="115,16" size="15,17" font="Regular;16" text="C" valign="center" halign="center" transparent="1" />
            <widget name="digicipher" position="132,16" size="25,17" font="Regular;16" text="DI" valign="center" halign="center" transparent="1" />
            <widget name="biss" position="155,16" size="60,17" font="Regular;16" text="BISS" valign="center" halign="center" transparent="1" />

            <widget name="ecmInfo" position="230,10" size="%d,20" font="Regular;16" valign="center" transparent="1" noWrap="1" />
        </screen>""" % (width, config.plugins.CCcamInfo.ecmInfoPositionZ.value, width - 230)

SYSTEMS = ["irdeto", "seca", "nagra", "via", "conax", "betacrypt", "crypto", "dreamcrypt", "nds", "drecrypt", "powervu", "verimatrix", "rosscrypt", "exset", "codicrypt", "digicipher", "biss"]


class EcmInfoLabel(Label):
    def __init__(self, text=""):
        Label.__init__(self, text)

    def notCrypted(self):
        self.instance.setForegroundColor(parseColor("#999999"))

    def crypted(self):
        self.instance.setForegroundColor(parseColor("#ff9c00"))

    def encrypted(self):
        self.instance.setForegroundColor(parseColor("#00d100"))


class EcmInfoScreenNew(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = ECMINFO_SKIN_NEW
        self.systemCaids = {"06": "irdeto",
                            "01": "seca",
                            "18": "nagra",
                            "05": "via",
                            "0B": "conax",
                            "17": "betacrypt",
                            "0D": "crypto",
                            "4A": "dreamcrypt",
                            "09": "nds",
                            "7B": "drecrypt",
                            "0E": "powervu",
                            "56": "verimatrix",
                            "A1": "rosscrypt",
                            "27": "exset",
                            "22": "codicrypt",
                            "07": "digicipher",
                            "26": "biss"}

        for x in SYSTEMS:
            self[x] = EcmInfoLabel()
        self["ecmInfo"] = Label()

        self.shown = False
        self.onShow.append(self._onShow)
        self.onHide.append(self._onHide)

        self.ecmTimer = eTimer()
        self.ecmTimer.timeout.get().append(self.parseEcmInfo)
        self.hideTimer = eTimer()
        self.hideTimer.timeout.get().append(self.hide)
        self.change = False
        self.onShow.append(self.movePosition)

    def movePosition(self):
        if self.instance:
            self.instance.move(ePoint(config.plugins.CCcamInfo.ecmInfoPositionX.value, config.plugins.CCcamInfo.ecmInfoPositionY.value))
            if not config.plugins.CCcamInfo.show_cryptoinfo.value:
                if not self.change:
                    self.change = True
                    self.instance.resize(eSize(*(MAX_X, MAX_Y)))
            elif self.change:
                self.change = False
                self.instance.resize(eSize(*(ORIGMAX_X, MAX_Y)))

    def _onShow(self):
        self.shown = True
        self.ecmTimer.start(1000, False)

    def _onHide(self):
        self.shown = False
        self.hideTimer.stop()
        self.ecmTimer.stop()

    def int2hex(self, int):
        return "%x" % int

    def refreshLabels(self):
        self.hideTimer.stop()
        self.hide()
        for x in SYSTEMS:
            self[x].notCrypted()
        self["ecmInfo"].setText("")

        service = self.session.nav.getCurrentService()
        if service:
            info = service and service.info()
            if info:
                caids = info.getInfoObject(iServiceInformation.sCAIDs)
                if caids:
                    if len(caids) > 0:
                        for caid in caids:
                            caid = self.int2hex(caid)
                            if len(caid) == 3:
                                caid = "0%s" % caid
                            caid = caid[:2]
                            caid = caid.upper()
                            if caid in self.systemCaids:
                                system = self.systemCaids.get(caid)
                                self[system].crypted()

                        self.show()
                        self.hideTimer.stop()
                        self.hideTimer.start(config.plugins.CCcamInfo.ecmInfoTime.value * 1000, True)

    def parseEcmInfoLine(self, line):
        if line.__contains__(":"):
            idx = line.index(":")
            line = line[idx + 1:]
            line = line.replace("\n", "")
            while line.startswith(" "):
                line = line[1:]
            while line.endswith(" "):
                line = line[:-1]
            return line
        else:
            return ""

    def ecmfile(self):
        info = {}
        ecm = ""
        if self.shown:
            try:
                f = open("/tmp/ecm.info", "r")
                ecm = f.readlines()
                f.close()
            except:
                try:
                    if fileExists("/tmp/ecm1.info"):
                        f = open("/tmp/ecm1.info", "r")
                        ecm = f.readlines()
                        f.close()
                    elif fileExists("/tmp/ecm0.info"):
                        f = open("/tmp/ecm1.info", "r")
                        ecm = f.readlines()
                        f.close()
                except:
                    pass
            if ecm:
                for line in ecm:
                    x = line.lower().find("msec")
                    if x != -1:
                        info["ecm time"] = line[0:x + 4]
                    else:
                        item = line.split(":", 1)
                        if len(item) > 1:
                            info[item[0].strip().lower()] = item[1].strip()
                        else:
                            if "caid" not in info:
                                x = line.lower().find("caid")
                                if x != -1:
                                    y = line.find(",")
                                    if y != -1:
                                        info["caid"] = line[x + 5:y]
        return info

    def parseEcmInfo(self):
        textvalue = ""
        if self.shown:
            service = service = self.session.nav.getCurrentService()
            if service:
                info = service and service.info()
                if info and info.getInfo(iServiceInformation.sIsCrypted):
                    if info.getInfoObject(iServiceInformation.sCAIDs):
                        textvalue = _("No parse cannot emu")
                        ecm_info = self.ecmfile()
                        if ecm_info:
                            caid = ecm_info.get("caid", "")
                            if caid and caid != "0x000":
                                c = caid.lstrip("0x")
                                if len(c) == 3:
                                    c = "0%s" % c
                                c = c[:2].upper()
                                if c in self.systemCaids:
                                    system = self.systemCaids.get(c)
                                    self[system].encrypted()
                            if not config.plugins.CCcamInfo.show_cryptoinfo.value:
                                self["ecmInfo"].setText(textvalue)
                                return
                            caid = caid.lstrip("0x")
                            caid = caid.upper()
                            caid = caid.zfill(4)
                            caid = "Caid: %s" % caid
                        # Provider wicard
                            provider = ecm_info.get("Provider", "")
                            provider = provider.lstrip("0x")
                            provider = provider.upper()
                            provider = provider.zfill(6)
                            provider = "Prov: %s" % provider
                        # hops
                            reader = ecm_info.get("reader", "")
                            reader = "%s" % reader
                        # oscam
                            prov = ecm_info.get("prov", "")
                            prov = prov.lstrip("0x")
                            prov = prov.upper()
                            prov = prov.zfill(6)
                            prov = "%s" % prov
                            from2 = ecm_info.get("from", "")
                            from2 = "%s" % from2
                            if from2 and len(from2) > config.plugins.CCcamInfo.serverNameLength.value:
                                from2 = "%s***" % from2[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                        # ecm time
                            ecm_time = ecm_info.get("ecm time", None)
                            if ecm_time:
                                if "msec" in ecm_time:
                                    ecm_time = "Ecm: %s " % ecm_time
                                else:
                                    ecm_time = "Ecm: %s s" % ecm_time
                        # address
                            address = ecm_info.get("address", "")
                            if address and len(address) > config.plugins.CCcamInfo.serverNameLength.value:
                                address = "%s***" % address[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                        # protocol
                            protocol = ecm_info.get("protocol", "")
                        # source
                            using = ecm_info.get("using", "")
                            if using:
                                if using == "emu":
                                    textvalue = "(EMU) %s - %s" % (caid, ecm_time)
                                elif using == "CCcam-s2s":
                                    textvalue = "(NET) %s - %s - %s - %s" % (caid, address, using, ecm_time)
                                else:
                                    textvalue = "%s - %s - %s - %s" % (caid, address, using, ecm_time)
                            else:
                                # mgcamd
                                source = ecm_info.get("source", None)
                                if source:
                                    if source == "emu":
                                        textvalue = "Source: EMU %s" % (caid)
                                    else:
                                        if len(source) > config.plugins.CCcamInfo.serverNameLength.value:
                                            source = "%s***" % source[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                                        textvalue = "%s Prov: %s - %s - %s" % (caid, prov, source, ecm_time)
                                # oscam
                                oscsource = ecm_info.get("reader", None)
                                if oscsource:
                                    if oscsource == "emu":
                                        textvalue = "Source: EMU %s" % (caid)
                                    else:
                                        textvalue = "Reader: %s ( %s Prov: %s - %s - %s - %s )" % (reader, caid,  prov, from2, ecm_time, protocol)
                                # wicardd
                                wicarddsource = ecm_info.get("response time", None)
                                if wicarddsource:
                                    if len(wicarddsource) > config.plugins.CCcamInfo.serverNameLength.value:
                                        wicarddsource = "%s***" % wicarddsource[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                                    textvalue = "%s - %s - %s" % (caid, provider, wicarddsource)
                                # gbox
                                decode = ecm_info.get("decode", None)
                                if decode:
                                    if decode == "Internal":
                                        textvalue = "(EMU) %s" % (caid)
                                    else:
                                        if len(decode) > config.plugins.CCcamInfo.serverNameLength.value:
                                            decode = "%s***" % decode[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                                        textvalue = "%s - %s" % (caid, decode)
            self["ecmInfo"].setText(textvalue)

    def parseEcmInfo1(self):
        if self.shown:
            ecmInfoString = ""
            using = ""
            address = ""
            hops = ""
            ecmTime = ""
            content = ""
            try:
                f = open("/tmp/ecm.info", "r")
                content = f.read()
                f.close()
            except:
                try:
                    f = open("/tmp/ecm1.info", "r")
                    content = f.read()
                    f.close()
                except:
                    pass

            contentInfo = content.split("\n")
            for line in contentInfo:
                if line.startswith("caid:"):
                    caid = self.parseEcmInfoLine(line)
                    if caid.__contains__("x"):
                        idx = caid.index("x")
                        caid = caid[idx + 1:]
                        if len(caid) == 3:
                            caid = "0%s" % caid
                        caid = caid[:2]
                        caid = caid.upper()
                        if caid in self.systemCaids:
                            system = self.systemCaids.get(caid)
                            self[system].encrypted()
                elif line.startswith("using:"):
                    using = self.parseEcmInfoLine(line)
                    if using == "fta":
                        using = _("Free to Air")
                elif line.startswith("address:"):
                    address = self.parseEcmInfoLine(line)
                    if len(address) > config.plugins.CCcamInfo.serverNameLength.value:
                        address = "%s***" % address[:config.plugins.CCcamInfo.serverNameLength.value - 3]
                elif line.startswith("hops:"):
                    hops = "%s %s" % (_("Hops:"), self.parseEcmInfoLine(line))
                elif line.startswith("ecm time:"):
                    ecmTime = "%s %s" % (_("Ecm time:"), self.parseEcmInfoLine(line))

            if using != "":
                ecmInfoString = "%s " % using
            if address != "":
                ecmInfoString = "%s%s " % (ecmInfoString, address)
            if hops != "":
                ecmInfoString = "%s%s " % (ecmInfoString, hops)
            if ecmTime != "":
                ecmInfoString = "%s%s " % (ecmInfoString, ecmTime)

            self["ecmInfo"].setText(ecmInfoString)


class EcmInfo():
    def __init__(self):
        self.dialog = None
        self.mayShow = True
        self.hideCallbackAdded = False

    def gotSession(self, session):
        if not self.dialog and session:
            self.dialog = session.instantiateDialog(EcmInfoScreenNew)
            InfoBar.toggleShow = self.toggleShow
        self.__event_tracker = ServiceEventTracker(screen=self.dialog, eventmap={iPlayableService.evUpdatedInfo: self.evUpdatedInfo, iPlayableService.evEnd: self.__evEnd})

    def evUpdatedInfo(self):
        if config.plugins.CCcamInfo.ecmInfoEnabled.value and self.mayShow:
            self.dialog.refreshLabels()

    def __evEnd(self):
        self.dialog and self.dialog.hide()

    def toggleShow(self):
        self.evUpdatedInfo()
        if InfoBar and InfoBar.instance:
            TOGGLE_SHOW(InfoBar.instance)
            if self.hideCallbackAdded is False:
                self.hideCallbackAdded = True
                InfoBar.instance.onHide.append(self._onHide)

    def _onHide(self):
        if config.plugins.CCcamInfo.ecmInfoForceHide.value:
            self.dialog.hide()


ecmInfo = EcmInfo()


class EcmInfoPositioner(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = ECMINFO_SKIN_NEW

        for x in SYSTEMS:
            self[x] = EcmInfoLabel()
        self["ecmInfo"] = Label("")

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"left": self.left,
                                     "up": self.up,
                                     "right": self.right,
                                     "down": self.down,
                                     "ok": self.ok,
                                     "cancel": self.exit}, -1)

        self.moveTimer = eTimer()
        self.moveTimer.timeout.get().append(self.movePosition)
        self.moveTimer.start(50, 1)

    def createLabels(self):
        for x in SYSTEMS:
            self[x].notCrypted()

    def movePosition(self):
        self.instance.move(ePoint(config.plugins.CCcamInfo.ecmInfoPositionX.value, config.plugins.CCcamInfo.ecmInfoPositionY.value))
        self.moveTimer.start(50, 1)

    def left(self):
        value = config.plugins.CCcamInfo.ecmInfoPositionX.value
        value -= 1
        if value < 0:
            value = 0
        config.plugins.CCcamInfo.ecmInfoPositionX.value = value

    def up(self):
        value = config.plugins.CCcamInfo.ecmInfoPositionY.value
        value -= 1
        if value < 0:
            value = 0
        config.plugins.CCcamInfo.ecmInfoPositionY.value = value

    def right(self):
        value = config.plugins.CCcamInfo.ecmInfoPositionX.value
        value += 1
        config.plugins.CCcamInfo.ecmInfoPositionX.value = value

    def down(self):
        value = config.plugins.CCcamInfo.ecmInfoPositionY.value
        value += 1
        config.plugins.CCcamInfo.ecmInfoPositionY.value = value

    def ok(self):
        config.plugins.CCcamInfo.ecmInfoPositionX.save()
        config.plugins.CCcamInfo.ecmInfoPositionY.save()
        self.close()

    def exit(self):
        config.plugins.CCcamInfo.ecmInfoPositionX.cancel()
        config.plugins.CCcamInfo.ecmInfoPositionY.cancel()
        self.close()


if width > 1280:
    EcmInfoConfigMenu_SKIN = """
    <screen name="" position="center,center" size="860,320" title="CCcam Info">
        <widget name="config" position="10,10" size="840,300" scrollbarMode="showOnDemand" font="Regular; 25" />
    </screen>"""
else:
    EcmInfoConfigMenu_SKIN = """
    <screen position="center,center" size="560,220" title="CCcam Info">
        <widget name="config" position="10,10" size="540,200" scrollbarMode="showOnDemand" />
    </screen>"""


class EcmInfoConfigMenu(ConfigListScreen, Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = EcmInfoConfigMenu_SKIN
        self.setTitle(_("Encoding screen config menu"))
        self.positionEntry = ConfigSelection(choices=["<>"], default="<>")
        ConfigListScreen.__init__(self, [
            getConfigListEntry(_("Activate screen:"), config.plugins.CCcamInfo.ecmInfoEnabled),
            getConfigListEntry(_("Show ecm.info:"), config.plugins.CCcamInfo.show_cryptoinfo),
            getConfigListEntry(_("Hide ecm.info after (x) seconds:"), config.plugins.CCcamInfo.ecmInfoTime),
            getConfigListEntry(_("Hide ecm.info with InfoBar:"), config.plugins.CCcamInfo.ecmInfoForceHide),
            getConfigListEntry(_("Cut servername after (x) letters:"), config.plugins.CCcamInfo.serverNameLength),
            getConfigListEntry(_("Z position screen:"), config.plugins.CCcamInfo.ecmInfoPositionZ),
            getConfigListEntry("X / Y " + _("Position:"), self.positionEntry),
            getConfigListEntry(_("Show CCcam Info in ext menu:"), config.plugins.CCcamInfo.showExtMenu)])

        self["actions"] = ActionMap(["CCcamInfoActions"], {"ok": self.okClicked, "cancel": self.exit}, -2)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.handleKeysLeftAndRight()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.handleKeysLeftAndRight()

    def handleKeysLeftAndRight(self):
        sel = self["config"].getCurrent()[1]
        if sel == self.positionEntry:
            self.checkEcmInfoSession()
            self.session.openWithCallback(self.ecmInfoPositionerCallback, EcmInfoPositioner)

    def ecmInfoPositionerCallback(self, callback=None):
        ecmInfo.mayShow = True

    def checkEcmInfoSession(self):
        if ecmInfo.dialog is None:
            ecmInfo.gotSession(self.session)
        ecmInfo.mayShow = False
        ecmInfo.dialog.hide()

    def okClicked(self):
        for x in self["config"].list:
            x[1].save()
        self.close()

    def exit(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()


class CCcamList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if width > 1280:
            self.l.setItemHeight(40)
            self.l.setFont(0, gFont("Regular", 28))
        else:
            self.l.setItemHeight(50)
            self.l.setFont(0, gFont("Regular", 28))


class CCcamShareList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if width > 1280:
            self.l.setItemHeight(110)
            self.l.setFont(0, gFont("Regular", 28))
        else:
            self.l.setItemHeight(60)
            self.l.setFont(0, gFont("Regular", 20))


class CCcamConfigList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if width > 1280:
            self.l.setItemHeight(50)
            self.l.setFont(0, gFont("Regular", 28))
        else:
            self.l.setItemHeight(40)
            self.l.setFont(0, gFont("Regular", 20))


class CCcamShareViewList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if width > 1280:
            self.l.setItemHeight(50)
            self.l.setFont(0, gFont("Regular", 28))
        else:
            self.l.setItemHeight(40)
            self.l.setFont(0, gFont("Regular", 20))


def CCcamListEntry(name, idx):
    res = [(name)]
    if idx == 10:
        idx = "red"
    elif idx == 11:
        idx = "green"
    elif idx == 12:
        idx = "yellow"
    elif idx == 13:
        idx = "blue"
    elif idx == 14:
        idx = "menu"
    elif idx == 15:
        idx = "info"

    png = plugin_path + "/icons/key_%s.png" % str(idx)

    if fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 9), size=(35, 25), png=loadPNG(png)))
    res.append(MultiContentEntryText(pos=(50, 3), size=(500, 40), font=0, text=name))
    return res


def CCcamServerListEntry(name, color):
    res = [(name)]
    png = plugin_path + "/icons/key_%s.png" % color
    if fileExists(png):
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 9), size=(35, 25), png=loadPNG(png)))
    res.append(MultiContentEntryText(pos=(50, 3), size=(500, 40), font=0, text=name))
    return res


def CCcamShareListEntry(hostname, type, caid, system, uphops, maxdown):
    res = [(hostname, type, caid, system, uphops, maxdown)]
    res.append(MultiContentEntryText(pos=(5, 5), size=(380, 35), font=0, text=hostname))
    res.append(MultiContentEntryText(pos=(450, 5), size=(300, 35), font=0, text=_("Type: ") + type, flags=RT_HALIGN_RIGHT))
    res.append(MultiContentEntryText(pos=(5, 35), size=(380, 35), font=0, text=_("CaID: ") + caid))
    res.append(MultiContentEntryText(pos=(450, 35), size=(300, 35), font=0, text=_("System: ") + system, flags=RT_HALIGN_RIGHT))
    res.append(MultiContentEntryText(pos=(5, 70), size=(380, 35), font=0, text=_("Uphops: ") + uphops))
    res.append(MultiContentEntryText(pos=(450, 70), size=(300, 35), font=0, text=_("Maxdown: ") + maxdown, flags=RT_HALIGN_RIGHT))
    return res


def CCcamShareViewListEntry(caidprovider, providername, numberofcards, numberofreshare):
    res = [(caidprovider, providername, numberofcards)]
    res.append(MultiContentEntryText(pos=(5, 5), size=(420, 40), font=0, text=providername))
    res.append(MultiContentEntryText(pos=(430, 5), size=(50, 40), font=0, text=numberofcards, flags=RT_HALIGN_RIGHT))
    res.append(MultiContentEntryText(pos=(480, 5), size=(50, 40), font=0, text=numberofreshare, flags=RT_HALIGN_RIGHT))
    return res


def CCcamConfigListEntry(file):
    res = [(file)]

    try:
        f = open(CFG, "r")
        org = f.read()
        f.close()
    except:
        org = ""

    (name, content) = getConfigNameAndContent(file)

    if content == org:
        png = lock_on
    else:
        png = lock_off

    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 9), size=(35, 25), png=png))
    res.append(MultiContentEntryText(pos=(40, 2), size=(550, 40), font=0, text=name))

    return res


def CCcamMenuConfigListEntry(name, blacklisted):
    res = [(name)]

    if blacklisted:
        png = lock_off
    else:
        png = lock_on

    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 9), size=(35, 25), png=png))
    res.append(MultiContentEntryText(pos=(40, 2), size=(550, 40), font=0, text=name))

    return res


if width > 1280:
    CCcamInfoMain_SKIN = """
    <screen position="center,center" size="800,620" title="CCcam Info">
        <widget name="menu" position="0,0" size="800,620" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoMain_SKIN = """
    <screen position="center,center" size="500,420" title="CCcam Info" >
        <widget name="menu" position="0,0" size="500,420" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoMain(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoMain_SKIN
        self.setTitle(_("CCcam Info Main"))
        self["menu"] = CCcamList([])

        self.working = False
        if NEW_CVS:
            self.Console = Console()

        if config.plugins.CCcamInfo.profile.value == "":
            self.readConfig()
        else:
            self.url = config.plugins.CCcamInfo.profile.value

        self["actions"] = NumberActionMap(["CCcamInfoActions"],
                                          {"1": self.keyNumberGlobal,
                                           "2": self.keyNumberGlobal,
                                           "3": self.keyNumberGlobal,
                                           "4": self.keyNumberGlobal,
                                           "5": self.keyNumberGlobal,
                                           "6": self.keyNumberGlobal,
                                           "7": self.keyNumberGlobal,
                                           "8": self.keyNumberGlobal,
                                           "9": self.keyNumberGlobal,
                                           "0": self.keyNumberGlobal,
                                           "red": self.red,
                                           "green": self.green,
                                           "yellow": self.yellow,
                                           "blue": self.blue,
                                           "menu": self.menu,
                                           "info": self.info,
                                           "ok": self.okClicked,
                                           "cancel": self.close,
                                           "up": self.up,
                                           "down": self.down,
                                           "left": self.left,
                                           "right": self.right}, -2)

        self.onLayoutFinish.append(self.updateMenuList)

    def updateMenuList(self):
        self.working = True

        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]

        list = []
        idx = 0
        for x in menu_list:
            if notBlackListed(x):
                list.append(CCcamListEntry(x, idx))
                self.menu_list.append(x)
                idx += 1

        self["menu"].setList(list)
        self.working = False

    def readConfig(self):
        self.url = "http://127.0.0.1:16001"

        username = None
        password = None

        try:
            f = open(CFG, 'r')

            for lx in f:
                if lx.startswith('WEBINFO LISTEN PORT :'):
                    port = getConfigValue(lx)
                    if port != "":
                        self.url = self.url.replace('16001', port)

                elif lx.startswith('WEBINFO USERNAME :'):
                    username = getConfigValue(lx)

                elif lx.startswith('WEBINFO PASSWORD :'):
                    password = getConfigValue(lx)

            f.close()
        except:
            pass
        if (username is not None) and (password is not None) and (username != "") and (password != ""):
            self.url = self.url.replace('http://', ("http://%s:%s@" % (username, password)))

        config.plugins.CCcamInfo.profile.value = ""
        config.plugins.CCcamInfo.profile.save()

    def profileSelected(self, url=None):
        if url is not None:
            self.url = url
            config.plugins.CCcamInfo.profile.value = self.url
            config.plugins.CCcamInfo.profile.save()
            self.showInfo(_("New profile: ") + url)
        else:
            self.showInfo(_("Using old profile: ") + self.url)

    def keyNumberGlobal(self, idx):
        if (self.working) is False and (idx < len(self.menu_list)):
            self.working = True
            sel = self.menu_list[idx]
            if sel == _("General"):
                getPage(self.url).addCallback(self.showCCcamGeneral).addErrback(self.getWebpageError)
            elif sel == _("Clients"):
                getPage(self.url + "/clients").addCallback(self.showCCcamClients).addErrback(self.getWebpageError)
            elif sel == _("Active clients"):
                getPage(self.url + "/activeclients").addCallback(self.showCCcamClients).addErrback(self.getWebpageError)
            elif sel == _("Servers"):
                getPage(self.url + "/servers").addCallback(self.showCCcamServers).addErrback(self.getWebpageError)
            elif sel == _("Shares"):
                getPage(self.url + "/shares").addCallback(self.showCCcamShares).addErrback(self.getWebpageError)
            elif sel == _("Share View"):
                self.session.openWithCallback(self.workingFinished, CCcamShareViewMenu, self.url)
            elif sel == _("Extended Shares"):
                self.session.openWithCallback(self.workingFinished, CCcamInfoShareInfo, "None", self.url)
            elif sel == _("Providers"):
                getPage(self.url + "/providers").addCallback(self.showCCcamProviders).addErrback(self.getWebpageError)
            elif sel == _("Entitlements"):
                getPage(self.url + "/entitlements").addCallback(self.showCCcamEntitlements).addErrback(self.getWebpageError)
            elif sel == _("ecm.info"):
                self.session.openWithCallback(self.showEcmInfoFile, CCcamInfoEcmInfoSelection)
            elif sel == _("Menu config"):
                self.session.openWithCallback(self.updateMenuList, CCcamInfoMenuConfig)
            elif sel == _("Local box"):
                self.readConfig()
                self.showInfo(_("Profile: Local box"))
            elif sel == _("Remote box"):
                self.session.openWithCallback(self.profileSelected, CCcamInfoRemoteBoxMenu)
            elif sel == _("CCcam Prio Maker"):
                self.session.openWithCallback(self.workingFinished, CCcamPrioMaker.Ccprio_Setup)
            elif sel == _("CCcam Organizer"):
                self.session.openWithCallback(self.workingFinished, CCcamOrganizer.OrganizerMenu)
            elif sel == _("Switch config"):
                self.session.openWithCallback(self.workingFinished, CCcamInfoConfigSwitcher)
            else:
                text = _("CCcam Info %s\nby AliAbdul, modified for Python3 by WanWizard %s\n") % (VERSION, DATE) + _("This plugin shows you the status of your CCcam.")
                self.showInfo(text)

    def red(self):
        self.keyNumberGlobal(10)

    def green(self):
        self.keyNumberGlobal(11)

    def yellow(self):
        self.keyNumberGlobal(12)

    def blue(self):
        self.keyNumberGlobal(13)

    def menu(self):
        self.keyNumberGlobal(14)

    def info(self):
        self.keyNumberGlobal(15)

    def okClicked(self):
        self.keyNumberGlobal(self["menu"].getSelectedIndex())

    def up(self):
        if self.working is False:
            self["menu"].up()

    def down(self):
        if self.working is False:
            self["menu"].down()

    def left(self):
        if self.working is False:
            self["menu"].pageUp()

    def right(self):
        if self.working is False:
            self["menu"].pageDown()

    def getWebpageError(self, error=""):
        print(str(error))
        self.session.openWithCallback(self.workingFinished, MessageBox, _("Error reading webpage!"), MessageBox.TYPE_ERROR)

    def showFile(self, file):
        try:
            f = open(file, "r")
            content = f.read()
            f.close()
        except:
            content = _("Could not open the file %s!") % file

        self.showInfo(translateBlock(content))

    def showEcmInfoFile(self, file=None):
        if file is not None:
            self.showFile("/tmp/" + file)
        self.workingFinished()

    def showCCcamGeneral(self, html):
        if html.__contains__('<BR><BR>'):
            idx = html.index('<BR><BR>')
            idx2 = html.index('<BR></BODY>')
            html = html[idx + 8:idx2].replace("<BR>", "\n").replace("\n\n", "\n")
            self.infoToShow = html
            getPage(self.url + "/shares").addCallback(self.showCCcamGeneral2).addErrback(self.getWebpageError)
        else:
            self.showInfo(_("Error reading webpage!"))

    def showCCcamGeneral2(self, html):
        if html.__contains__("Welcome to CCcam"):
            idx = html.index("Welcome to CCcam")
            html = html[idx + 17:]
            idx = html.index(" ")
            version = html[:idx]
            self.infoToShow = "%s%s\n%s" % (_("Version: "), version, self.infoToShow)

        if html.__contains__("Available shares:"):
            idx = html.index("Available shares:")
            html = html[idx + 18:]
            idx = html.index("\n")
            html = html[:idx]
            self.showInfo(translateBlock("%s %s\n%s" % (_("Available shares:"), html, self.infoToShow)))
        else:
            self.showInfo(translateBlock(self.infoToShow))

    def showCCcamClients(self, html):
        firstLine = True
        clientList = []
        infoList = []
        lines = html.split("\n")

        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split('|')
                    if len(list) > 8:
                        username = list[1].replace(" ", "")
                        if username != "":
                            hostname = list[2].replace(" ", "")
                            connected = list[3].replace(" ", "")
                            idleTime = list[4].replace(" ", "")
                            ecm = list[5].replace(" ", "")
                            emm = list[6].replace(" ", "")
                            version = list[7].replace(" ", "")
                            share = list[8].replace(" ", "")

                            if version == "":
                                version = "N/A"

                            ecmEmm = "ECM: " + ecm + " - EMM: " + emm

                            infoList.append([username, _("Hostname: ") + hostname, _("Connected: ") + connected, _("Idle Time: ") + idleTime, _("Version: ") + version, _("Last used share: ") + share, ecmEmm])
                            clientList.append(username)

        self.openSubMenu(clientList, infoList)

    def showCCcamServers(self, html):
        firstLine = True
        infoList = []
        lines = html.split("\n")

        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split('|')
                    if len(list) > 7:
                        hostname = list[1].replace(" ", "")
                        if hostname != "":
                            connected = list[2].replace(" ", "")
                            type = list[3].replace(" ", "")
                            version = list[4].replace(" ", "")
                            nodeid = list[5].replace(" ", "")
                            cards = list[6].replace(" ", "")

                            if version == "":
                                version = "N/A"

                            if nodeid == "":
                                nodeid = "N/A"

                            infoList.append([hostname, _("Cards: ") + cards, _("Type: ") + type, _("Version: ") + version, _("NodeID: ") + nodeid, _("Connected: ") + connected])

        self.session.openWithCallback(self.workingFinished, CCcamInfoServerMenu, infoList, self.url)

    def showCCcamShares(self, html):
        firstLine = True
        sharesList = []
        infoList = []
        lines = html.split("\n")

        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split('|')
                    if len(list) > 7:
                        hostname = list[1].replace(" ", "")
                        if hostname != "":
                            type = list[2].replace(" ", "")
                            caid = list[3].replace(" ", "")
                            system = list[4].replace(" ", "")

                            string = list[6]
                            while string.startswith(" "):
                                string = string[1:]

                            while string.endswith(" "):
                                string = string[:-1]

                            idx = string.index(" ")
                            uphops = string[:idx]
                            string = string[idx + 1:]

                            while string.startswith(" "):
                                string = string[1:]
                            maxdown = string

                            if len(caid) == 3:
                                caid = "0" + caid

                            infoList.append([hostname, _("Type: ") + type, _("CaID: ") + caid, _("System: ") + system, _("Uphops: ") + uphops, _("Maxdown: ") + maxdown])
                            sharesList.append(hostname + " - " + _("CaID: ") + caid)

        self.openSubMenu(sharesList, infoList)

    def showCCcamProviders(self, html):
        firstLine = True
        providersList = []
        infoList = []
        lines = html.split("\n")

        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split('|')
                    if len(list) > 5:
                        caid = list[1].replace(" ", "")
                        if caid != "":
                            provider = list[2].replace(" ", "")
                            providername = list[3].replace(" ", "")
                            system = list[4].replace(" ", "")

                            infoList.append([_("CaID: ") + caid, _("Provider: ") + provider, _("Provider Name: ") + providername, _("System: ") + system])
                            providersList.append(_("CaID: ") + caid + " - " + _("Provider: ") + provider)

        self.openSubMenu(providersList, infoList)

    def showCCcamEntitlements(self, html):
        if html.__contains__('<PRE>'):
            idx = html.index('<PRE>')
            idx2 = html.index('</PRE>')
            html = html[idx + 5:idx2].replace("\n\n", "\n")

            if html == "":
                html = _("No card inserted!")

            self.showInfo(translateBlock(html))
        else:
            self.showInfo(_("Error reading webpage!"))

    def showInfo(self, info):
        self.session.openWithCallback(self.workingFinished, CCcamInfoInfoScreen, info)

    def openSubMenu(self, list, infoList):
        self.session.openWithCallback(self.workingFinished, CCcamInfoSubMenu, list, infoList)

    def workingFinished(self, callback=None):
        self.working = False


if width > 1280:
    CCcamInfoEcmInfoSelection_SKIN = """
    <screen name="" position="center,center" size="800,620" title="CCcam Info">
        <widget name="list" position="0,0" size="800,620" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoEcmInfoSelection_SKIN = """
    <screen position="center,center" size="500,420" title="CCcam Info" >
        <widget name="list" position="0,0" size="500,420" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoEcmInfoSelection(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = CCcamInfoEcmInfoSelection_SKIN
        self.setTitle(_("ecm.info selection"))
        list = []
        tmp = listdir("/tmp/")
        for x in tmp:
            if x.endswith('.info') and x.startswith('ecm'):
                list.append(x)
        self["list"] = MenuList(list)

        self["actions"] = ActionMap(["CCcamInfoActions"], {"ok": self.ok, "cancel": self.close}, -1)

    def ok(self):
        self.close(self["list"].getCurrent())


if width > 1280:
    CCcamInfoInfoScreen_SKIN = """
    <screen position="center,center" size="800,620" title="CCcam Info">
        <widget name="text" position="0,0" size="800,620" font="Regular; 30" />
    </screen>"""
else:
    CCcamInfoInfoScreen_SKIN = """
    <screen position="center,center" size="500,420" title="CCcam Info" >
        <widget name="text" position="0,0" size="500,420" font="Regular;20" />
    </screen>"""


class CCcamInfoInfoScreen(Screen):

    def __init__(self, session, info):
        Screen.__init__(self, session)
        self.skin = CCcamInfoInfoScreen_SKIN
        self.setTitle(_("CCcam Info"))
        self["text"] = ScrollLabel(info)

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"ok": self.close,
                                     "cancel": self.close,
                                     "up": self["text"].pageUp,
                                     "down": self["text"].pageDown,
                                     "left": self["text"].pageUp,
                                     "right": self["text"].pageDown}, -1)


if width > 1280:
    CCcamShareViewMenu_SKIN = """
    <screen position="center,center" size="860,700" title="CCcam Info">
        <widget name="list" position="0,0" size="860,565" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,567" size="840,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="uphops" position="19,574" size="400,40" font="Regular; 30" />
        <widget name="cards" position="438,574" size="400,40" halign="right" font="Regular; 30" />
        <widget name="providers" position="19,615" size="400,40" font="Regular; 30" />
        <widget name="reshare" position="438,615" size="400,40" halign="right" font="Regular; 30" />
        <widget name="title" position="0,655" size="860,40" halign="center" font="Regular; 30" />
    </screen>"""
else:
    CCcamShareViewMenu_SKIN = """
    <screen position="center,center" size="560,430" title="CCcam Info" >
        <widget name="list" position="0,0" size="560,320" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,322" size="540,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="uphops" position="10,340" size="260,25" font="Regular;20" />
        <widget name="cards" position="290,340" size="260,25" halign="right" font="Regular;20" />
        <widget name="providers" position="10,370" size="260,25" font="Regular;20" />
        <widget name="reshare" position="290,370" size="260,25" halign="right" font="Regular;20" />
        <widget name="title" position="0,400" size="560,20" halign="center" font="Regular;20" />
    </screen>"""


class CCcamShareViewMenu(Screen, HelpableScreen):

    def __init__(self, session, url):
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        self.session = session
        self.skin = CCcamShareViewMenu_SKIN
        self.setTitle(_("CCcam Share View Menu"))
        self.url = url
        self.list = []
        self.providers = {}
        self.uphop = -1
        self.working = True
        self["list"] = CCcamShareViewList([])
        self["uphops"] = Label()
        self["cards"] = Label()
        self["providers"] = Label()
        self["reshare"] = Label()
        self["title"] = Label()

        self["actions"] = HelpableNumberActionMap(self, "CCcamInfoActions",
                                                  {"cancel": (self.exit, _("close share view")),
                                                   "0": (self.getUphop, _("show cards with uphop 0")),
                                                   "1": (self.getUphop, _("show cards with uphop 1")),
                                                   "2": (self.getUphop, _("show cards with uphop 2")),
                                                   "3": (self.getUphop, _("show cards with uphop 3")),
                                                   "4": (self.getUphop, _("show cards with uphop 4")),
                                                   "5": (self.getUphop, _("show cards with uphop 5")),
                                                   "6": (self.getUphop, _("show cards with uphop 6")),
                                                   "7": (self.getUphop, _("show cards with uphop 7")),
                                                   "8": (self.getUphop, _("show cards with uphop 8")),
                                                   "9": (self.getUphop, _("show cards with uphop 9")),
                                                   "green": (self.showAll, _("show all cards")),
                                                   "incUphop": (self.incUphop, _("increase uphop by 1")),
                                                   "decUphop": (self.decUphop, _("decrease uphop by 1")),
                                                   "ok": (self.getServer, _("get the cards' server"))}, -1)

        self.onLayoutFinish.append(self.getProviders)

    def exit(self):
        if self.working is False:
            self.close()

    def getProviders(self):
        getPage(self.url + "/providers").addCallback(self.readProvidersCallback).addErrback(self.readError)

    def readError(self, error=None):
        self.session.open(MessageBox, _("Error reading webpage!"), MessageBox.TYPE_ERROR)
        self.working = False

    def readSharesCallback(self, html):
        firstLine = True
        providerList = []
        countList = []
        shareList = []
        reshareList = []
        self.hostList = []
        self.caidList = []
        count = 0
        totalcards = 0
        totalproviders = 0
        resharecards = 0
        numberofreshare = 0
        ulevel = 0
        lines = html.split("\n")
        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split("|")
                    if len(list) > 7:
                        hostname = list[1].replace(" ", "")
                        if hostname != "":
                            if self.uphop == -1:
                                caid = list[3].replace(" ", "")
                                provider = list[5].replace(" ", "")
                                caidprovider = self.formatCaidProvider(caid, provider)
                                string = list[6]
                                while string.startswith(" "):
                                    string = string[1:]

                                while string.endswith(" "):
                                    string = string[:-1]

                                idx = string.index(" ")
                                maxdown = string[idx + 1:]

                                while maxdown.startswith(" "):
                                    maxdown = maxdown[1:]
                                    down = maxdown

                                if caidprovider not in providerList:
                                    providerList.append(caidprovider)
                                    count = 1
                                    countList.append(count)
                                    numberofcards = count
                                    providername = self.providers.get(caidprovider, 'Multiple Providers given')
                                    # if providername == 'Multiple Providers given':
                                        # print caidprovider
                                    numberofreshare = 0
                                    if int(down) > 0:
                                        resharecards += 1
                                        numberofreshare = 1
                                    reshareList.append(numberofreshare)

                                    shareList.append(CCcamShareViewListEntry(caidprovider, providername, str(numberofcards), str(numberofreshare)))
                                    self.list.append([caidprovider, providername, numberofcards,  numberofreshare])

                                    totalproviders += 1

                                elif caidprovider in providerList:
                                    i = providerList.index(caidprovider)
                                    count = countList[i]
                                    count += 1
                                    countList[i] = count
                                    numberofcards = count

                                    if int(down) > 0:
                                        reshare = reshareList[i]
                                        reshare += 1
                                        reshareList[i] = reshare
                                        numberofreshare = 0
                                        numberofreshare = reshare
                                        resharecards += 1
                                    elif int(down) == 0:
                                        numberofreshare = reshareList[i]

                                    providername = self.providers.get(caidprovider, 'Multiple Providers given')
                                    shareList[i] = CCcamShareViewListEntry(caidprovider, providername, str(numberofcards), str(numberofreshare))

                                self.hostList.append(hostname)
                                self.caidList.append(caidprovider)

                                totalcards += 1

                                ulevel = _("All")

                            else:
                                updown = list[6]
                                while updown.startswith(" "):
                                    updown = updown[1:]

                                while updown.endswith(" "):
                                    updown = updown[:-1]

                                idx = updown.index(" ")
                                up = updown[:idx]

                                maxdown = updown[idx + 1:]

                                while maxdown.startswith(" "):
                                    maxdown = maxdown[1:]
                                    down = maxdown

                                ulevel = str(self.uphop)

                                if int(up) == self.uphop:
                                    caid = list[3].replace(" ", "")
                                    provider = list[5].replace(" ", "")
                                    caidprovider = self.formatCaidProvider(caid, provider)
                                    if caidprovider not in providerList:
                                        providerList.append(caidprovider)
                                        count = 1
                                        countList.append(count)
                                        numberofcards = count
                                        providername = self.providers.get(caidprovider, 'Multiple Providers given')
                                        # if providername == 'Multiple Providers given':
                                            # print caidprovider

                                        numberofreshare = 0
                                        if int(down) > 0:
                                            resharecards += 1
                                            numberofreshare = 1
                                        reshareList.append(numberofreshare)

                                        shareList.append(CCcamShareViewListEntry(caidprovider, providername, str(numberofcards), str(numberofreshare)))
                                        self.list.append([caidprovider, providername, numberofcards, numberofreshare])

                                        totalproviders += 1
                                    elif caidprovider in providerList:
                                        i = providerList.index(caidprovider)
                                        count = countList[i]
                                        count += 1
                                        countList[i] = count
                                        numberofcards = count

                                        if int(down) > 0:
                                            reshare = reshareList[i]
                                            reshare += 1
                                            # if caidprovider == "05021700":
                                                # print "re: %d" %(reshare)
                                            reshareList[i] = reshare
                                            numberofreshare = 0
                                            numberofreshare = reshare
                                            resharecards += 1
                                        elif int(down) == 0:
                                            numberofreshare = reshareList[i]

                                        providername = self.providers.get(caidprovider, 'Multiple Providers given')
                                        shareList[i] = CCcamShareViewListEntry(caidprovider, providername, str(numberofcards), str(numberofreshare))

                                    self.hostList.append(hostname)
                                    self.caidList.append(caidprovider)
                                    totalcards += 1
                                    '''
                                    # maxdown = list[6]
                                    # while maxdown.startswith(" "):
                                        # maxdown = maxdown[1:]
                                        # down = maxdown
                                    # if int(down) > 0:
                                        # resharecards += 1
                                    '''

        self.instance.setTitle("%s (%s %d) %s %s" % (_("Share View"), _("Total cards:"), totalcards, _("Hops:"), ulevel))
        self["title"].setText("%s (%s %d) %s %s" % (_("Share View"), _("Total cards:"), totalcards, _("Hops:"), ulevel))
        self["list"].setList(shareList)
        self["uphops"].setText("%s %s" % (_("Hops:"), ulevel))
        self["cards"].setText("%s %s" % (_("Total cards:"), totalcards))
        self["providers"].setText("%s %s" % (_("Providers:"), totalproviders))
        self["reshare"].setText("%s %d" % (_("Reshare:"), resharecards))
        self.working = False

    def readProvidersCallback(self, html):
        firstLine = True
        lines = html.split("\n")
        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split('|')
                    if len(list) > 5:
                        caid = list[1].replace(" ", "")
                        if caid != "":
                            provider = list[2].replace(" ", "")
                            providername = list[3]
                            caidprovider = self.formatCaidProvider(caid, provider)
                            self.providers.setdefault(caidprovider, providername)
        getPage(self.url + "/shares").addCallback(self.readSharesCallback).addErrback(self.readError)

    def formatCaidProvider(self, caid, provider):
        pos = provider.find(",")
        if pos != -1:
            provider = provider[pos + 1:]
            pos = provider.find(",")
            if pos != -1:
                provider = provider[0:pos]

        if len(provider) == 0:
            provider = "0000"
        elif len(provider) == 1:
            provider = "000" + provider
        elif len(provider) == 2:
            provider = "00" + provider
        elif len(provider) == 3:
            provider = "0" + provider

        if len(caid) == 3:
            caid = "0" + caid

        if caid.startswith("0500") and len(provider) == 5:
            caid = "050"
        elif caid.startswith("0500") and len(provider) == 6:
            caid = "05"

        if caid.startswith("06"):
            caidprovider = caid
        elif caid.startswith("0d22"):
            caidprovider = caid
        elif caid.startswith("0d05"):
            caidprovider = caid
        elif caid.startswith("09"):
            caidprovider = caid
        elif caid.startswith("17"):
            caidprovider = caid
        elif caid.startswith("18"):
            caidprovider = caid
        elif caid.startswith("4a"):
            caidprovider = caid
        else:
            caidprovider = caid + provider
        return caidprovider

    def getUphop(self, uphop):
        self.uphop = uphop
        self.getProviders()

    def showAll(self):
        self.uphop = -1
        self.getProviders()

    def incUphop(self):
        if self.uphop < 9:
            self.uphop += 1
            self.getProviders()

    def decUphop(self):
        if self.uphop > -1:
            self.uphop -= 1
            self.getProviders()

    def getServer(self):
        server = _("Servers:") + " \n"
        sel = self["list"].getCurrent()
        if sel is not None:
            e = 0
            while e < len(self.caidList):
                if sel[0][0] == self.caidList[e]:
                    pos = self.hostList[e].find(":")
                    if pos != -1:
                        server += self.hostList[e][0:pos] + "\n"
                    else:
                        server += self.hostList[e] + "\n"
                e += 1
            self.session.open(CCcamInfoInfoScreen, server)


if width > 1280:
    CCcamInfoSubMenu_SKIN = """
    <screen position="center,center" size="800,620" title="CCcam Info">
        <widget name="list" position="0,0" size="800,330" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,332" size="780,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="info" position="0,335" size="800,280" font="Regular; 25" transparent="1" />
    </screen>"""
else:
    CCcamInfoSubMenu_SKIN = """
    <screen position="center,center" size="500,420" title="CCcam Info" >
        <widget name="list" position="0,0" size="500,250" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,252" size="480,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="info" position="0,255" size="500,165" font="Regular;16" transparent="1" />
    </screen>"""


class CCcamInfoSubMenu(Screen):

    def __init__(self, session, list, infoList):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoSubMenu_SKIN
        self.setTitle(_("CCcam Info Sub Menu"))
        self.infoList = infoList
        self["list"] = MenuList(list)
        self["info"] = Label()

        self["actions"] = ActionMap(["CCcamInfoActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

        self["list"].onSelectionChanged.append(self.showInfo)
        self.onLayoutFinish.append(self.showInfo)

    def okClicked(self):
        info = self.getInfo()
        if info != "":
            self.session.open(MessageBox, info, MessageBox.TYPE_INFO)

    def showInfo(self):
        info = self.getInfo()
        self["info"].setText(info)

    def getInfo(self):
        try:
            idx = self["list"].getSelectedIndex()
            info = ""
            infoList = self.infoList[idx]
            for x in infoList:
                info += x + "\n"
            return info
        except:
            return ""


if width > 1280:
    CCcamInfoServerMenu_SKIN = """
    <screen position="center,center" size="800,620" title="CCcam Info">
        <widget name="list" position="0,0" size="800,330" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,332" size="780,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="info" position="0,335" size="800,280" font="Regular;25" transparent="1" />
    </screen>"""
else:
    CCcamInfoServerMenu_SKIN = """
    <screen position="center,center" size="500,420" title="CCcam Info" >
        <widget name="list" position="0,0" size="500,250" scrollbarMode="showOnDemand" />
        <eLabel text="" position="10,252" size="480,2" font="Regular;14" backgroundColor="#ffffff" />
        <widget name="info" position="0,255" size="500,165" font="Regular;16" transparent="1" />
    </screen>"""


class CCcamInfoServerMenu(Screen):

    def __init__(self, session, infoList, url):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoServerMenu_SKIN
        self.setTitle(_("CCcam Info Server Menu"))
        self.infoList = infoList
        self.url = url

        list = []
        for x in self.infoList:
            if x[5].replace(_("Connected: "), "") == "":  # offline - red
                list.append(CCcamServerListEntry(x[0], "red"))
            elif x[1] == _("Cards: 0"):  # online with no card - blue
                list.append(CCcamServerListEntry(x[0], "blue"))
            else:  # online with cards - green
                list.append(CCcamServerListEntry(x[0], "green"))
        self["list"] = CCcamList(list)
        self["info"] = Label()

        self["actions"] = ActionMap(["CCcamInfoActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

        self["list"].onSelectionChanged.append(self.showInfo)
        self.onLayoutFinish.append(self.showInfo)

    def showInfo(self):
        info = self.getInfo()
        self["info"].setText(info)

    def getInfo(self):
        try:
            idx = self["list"].getSelectedIndex()

            info = ""
            infoList = self.infoList[idx]
            for x in infoList:
                info += x + "\n"

            return info
        except:
            return ""

    def okClicked(self):
        sel = self["list"].getCurrent()
        if sel is not None:
            self.session.open(CCcamInfoShareInfo, sel[0], self.url)


class CCcamInfoRemoteBox:
    def __init__(self, name, ip, username, password, port):
        self.name = name
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port


if width > 1280:
    CCcamInfoConfigMenu_SKIN = """
    <screen position="center,center" size="700,250" title="CCcam Info">
        <widget name="config" position="0,0" size="700,250" scrollbarMode="showOnDemand" font="Regular; 25" />
    </screen>"""
else:
    CCcamInfoConfigMenu_SKIN = """
    <screen position="center,center" size="560,150" title="CCcam Info">
        <widget name="config" position="0,0" size="560,150" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoConfigMenu(ConfigListScreen, Screen):

    def __init__(self, session, profile):
        Screen.__init__(self, session)
        self.skin = CCcamInfoConfigMenu_SKIN
        self.setTitle(_("CCcam Info Config Menu"))
        config.plugins.CCcamInfo.name.value = profile.name
        config.plugins.CCcamInfo.ip.value = profile.ip
        config.plugins.CCcamInfo.username.value = profile.username
        config.plugins.CCcamInfo.password.value = profile.password
        config.plugins.CCcamInfo.port.value = profile.port

        ConfigListScreen.__init__(self, [
            getConfigListEntry(_("Name:"), config.plugins.CCcamInfo.name),
            getConfigListEntry(_("IP:"), config.plugins.CCcamInfo.ip),
            getConfigListEntry(_("Username:"), config.plugins.CCcamInfo.username),
            getConfigListEntry(_("Password:"), config.plugins.CCcamInfo.password),
            getConfigListEntry(_("Port:"), config.plugins.CCcamInfo.port)])

        self["actions"] = ActionMap(["CCcamInfoActions"], {"ok": self.okClicked, "cancel": self.exit}, -2)

    def okClicked(self):
        self.close(CCcamInfoRemoteBox(config.plugins.CCcamInfo.name.value, config.plugins.CCcamInfo.ip.value, config.plugins.CCcamInfo.username.value, config.plugins.CCcamInfo.password.value, config.plugins.CCcamInfo.port.value))

    def exit(self):
        self.close(None)


if width > 1280:
    CCcamInfoRemoteBoxMenu_SKIN = """
    <screen position="center,center" size="860,620" title="CCcam Info">
        <ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="235,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="445,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="655,0" size="180,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="20,0" zPosition="1" size="180,40" font="Regular; 30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="235,0" zPosition="1" size="180,40" font="Regular; 30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="445,0" zPosition="1" size="180,40" font="Regular; 30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="655,0" zPosition="1" size="180,40" font="Regular; 30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="860,565" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoRemoteBoxMenu_SKIN = """
    <screen position="center,center" size="560,420" title="CCcam Info" >
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoRemoteBoxMenu(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoRemoteBoxMenu_SKIN
        self.setTitle(_("CCcam Info Remote Box Menu"))
        self.list = []
        self.profiles = []

        self["key_red"] = Label(_("Delete"))
        self["key_green"] = Label(_("New"))
        self["key_yellow"] = Label(_("Location"))
        self["key_blue"] = Label(_("Edit"))
        self["list"] = MenuList([])

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"cancel": self.exit,
                                     "ok": self.profileSelected,
                                     "red": self.delete,
                                     "green": self.new,
                                     "yellow": self.location,
                                     "blue": self.edit}, -1)

        self.onLayoutFinish.append(self.readProfiles)

    def readProfiles(self):
        try:
            f = open(config.plugins.CCcamInfo.profiles.value, "r")
            content = f.read()
            f.close()
        except:
            content = ""
        profiles = content.split("\n")
        for profile in profiles:
            if profile.__contains__("|"):
                tmp = profile.split("|")
                if len(tmp) == 5:
                    name = tmp[0]
                    ip = tmp[1]
                    username = tmp[2]
                    password = tmp[3]
                    port = int(tmp[4])
                    self.list.append(name)
                    self.profiles.append(CCcamInfoRemoteBox(name, ip, username, password, port))
        self["list"].setList(self.list)

    def saveConfigs(self):
        content = ""
        for x in self.profiles:
            content = "%s\n%s|%s|%s|%s|%d" % (content, x.name, x.ip, x.username, x.password, x.port)
        try:
            f = open(config.plugins.CCcamInfo.profiles.value, "w")
            f.write(content)
            f.close()
        except:
            pass

    def exit(self):
        self.saveConfigs()
        self.close(None)

    def profileSelected(self):
        self.saveConfigs()
        if len(self.list) > 0:
            idx = self["list"].getSelectionIndex()
            cur = self.profiles[idx]
            if cur.ip == "":
                url = None
            else:
                if cur.username != "" and cur.password != "":
                    url = "http://%s:%s@%s:%d" % (cur.username, cur.password, cur.ip, cur.port)
                else:
                    url = "http://%s:%d" % (cur.ip, cur.port)
            self.close(url)

    def delete(self):
        if len(self.list) > 0:
            idx = self["list"].getSelectionIndex()
            del self.list[idx]
            del self.profiles[idx]
            self["list"].setList(self.list)

    def new(self):
        self.session.openWithCallback(self.newCallback, CCcamInfoConfigMenu, CCcamInfoRemoteBox("Profile", "192.168.2.12", "", "", 16001))

    def newCallback(self, callback):
        if callback:
            self.list.append(callback.name)
            self.profiles.append(callback)
            self["list"].setList(self.list)

    def location(self):
        self.session.openWithCallback(self.locationCallback, LocationBox)

    def locationCallback(self, callback):
        if callback:
            config.plugins.CCcamInfo.profiles.value = ("%s/CCcamInfo.profiles" % callback).replace("//", "/")
            config.plugins.CCcamInfo.profiles.save()
        del self.list
        self.list = []
        del self.profiles
        self.profiles = []
        self.readProfiles()

    def edit(self):
        if len(self.list) > 0:
            idx = self["list"].getSelectionIndex()
            self.session.openWithCallback(self.editCallback, CCcamInfoConfigMenu, self.profiles[idx])

    def editCallback(self, callback):
        if callback:
            idx = self["list"].getSelectionIndex()
            del self.list[idx]
            del self.profiles[idx]
            self.list.append(callback.name)
            self.profiles.append(callback)
            self["list"].setList(self.list)


if width > 1280:
    CCcamInfoShareInfo_SKIN = """
    <screen position="center,center" size="860,620" title="CCcam Info">
        <ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="235,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="445,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="655,0" size="180,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="20,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="235,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="445,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="655,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="860,565" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoShareInfo_SKIN = """
    <screen position="center,center" size="560,420" title="CCcam Info" >
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoShareInfo(Screen):

    def __init__(self, session, hostname, url):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoShareInfo_SKIN
        self.setTitle(_("CCcam Share Info"))
        self.hostname = hostname
        self.url = url
        self.list = []
        self.uphops = -1
        self.maxdown = -1
        self.working = True

        self["key_red"] = Label(_("Uphops +"))
        self["key_green"] = Label(_("Uphops -"))
        self["key_yellow"] = Label(_("Maxdown +"))
        self["key_blue"] = Label(_("Maxdown -"))
        self["list"] = CCcamShareList([])

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"cancel": self.exit,
                                     "red": self.uhopsPlus,
                                     "green": self.uhopsMinus,
                                     "yellow": self.maxdownPlus,
                                     "blue": self.maxdownMinus}, -1)

        self.onLayoutFinish.append(self.readShares)

    def exit(self):
        if self.working is False:
            self.close()

    def readShares(self):
        getPage(self.url + "/shares").addCallback(self.readSharesCallback).addErrback(self.readSharesError)

    def readSharesError(self, error=None):
        self.session.open(MessageBox, _("Error reading webpage!"), MessageBox.TYPE_ERROR)
        self.working = False

    def readSharesCallback(self, html):
        firstLine = True
        shareList = []
        count = 0
        lines = html.split("\n")

        for lx in lines:
            if lx.__contains__('|'):
                if firstLine:
                    firstLine = False
                else:
                    list = lx.split("|")
                    if len(list) > 7:
                        hostname = list[1].replace(" ", "")
                        if (self.hostname == "None" or self.hostname == hostname) and hostname != "":
                            type = list[2].replace(" ", "")
                            caid = list[3].replace(" ", "")
                            system = list[4].replace(" ", "")

                            string = list[6]
                            while string.startswith(" "):
                                string = string[1:]

                            while string.endswith(" "):
                                string = string[:-1]

                            idx = string.index(" ")
                            uphops = string[:idx]
                            string = string[idx + 1:]

                            while string.startswith(" "):
                                string = string[1:]
                            maxdown = string

                            if len(caid) == 3:
                                caid = "0" + caid

                            shareList.append(CCcamShareListEntry(hostname, type, caid, system, uphops, maxdown))
                            self.list.append([hostname, type, caid, system, uphops, maxdown])
                            count += 1

        if self.uphops < 0:
            textUhops = _("All")
        else:
            textUhops = str(self.uphops)

        if self.maxdown < 0:
            textMaxdown = _("All")
        else:
            textMaxdown = str(self.maxdown)

        self.instance.setTitle("%s %d (%s%s / %s%s)" % (_("Available shares:"), count, _("Uphops: "), textUhops, _("Maxdown: "), textMaxdown))
        self["list"].setList(shareList)
        self.working = False

    def uhopsPlus(self):
        if self.working is False:
            self.uphops += 1
            if self.uphops > 9:
                self.uphops = -1
            self.refreshList()

    def uhopsMinus(self):
        if self.working is False:
            self.uphops -= 1
            if self.uphops < -1:
                self.uphops = 9
            self.refreshList()

    def maxdownPlus(self):
        if self.working is False:
            self.maxdown += 1
            if self.maxdown > 9:
                self.maxdown = -1
            self.refreshList()

    def maxdownMinus(self):
        if self.working is False:
            self.maxdown -= 1
            if self.maxdown < -1:
                self.maxdown = 9
            self.refreshList()

    def refreshList(self):
        shareList = []
        count = 0
        self.working = True

        for x in self.list:
            (hostname, type, caid, system, uphops, maxdown) = x
            if (uphops == str(self.uphops) or self.uphops == -1) and (maxdown == str(self.maxdown) or self.maxdown == -1):
                shareList.append(CCcamShareListEntry(hostname, type, caid, system, uphops, maxdown))
                count += 1

        if self.uphops < 0:
            textUhops = _("All")
        else:
            textUhops = str(self.uphops)

        if self.maxdown < 0:
            textMaxdown = _("All")
        else:
            textMaxdown = str(self.maxdown)

        self.instance.setTitle("%s %d (%s%s / %s%s)" % (_("Available shares:"), count, _("Uphops: "), textUhops, _("Maxdown: "), textMaxdown))
        self["list"].setList(shareList)
        self.working = False


if width > 1280:
    CCcamInfoConfigSwitcher_SKIN = """
    <screen position="center,center" size="860,620" title="CCcam Info">
        <ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="235,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="445,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="655,0" size="180,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="20,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="235,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="445,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="655,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="860,565" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoConfigSwitcher_SKIN = """
    <screen position="center,center" size="560,420" title="CCcam Info" >
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoConfigSwitcher(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoConfigSwitcher_SKIN
        self.setTitle(_("CCcam Config Switcher"))
        self["key_red"] = Label(_("Delete"))
        self["key_green"] = Label(_("Activate"))
        self["key_yellow"] = Label(_("Rename"))
        self["key_blue"] = Label(_("Content"))
        self["list"] = CCcamConfigList([])

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"ok": self.activate,
                                     "cancel": self.close,
                                     "red": self.delete,
                                     "green": self.activate,
                                     "yellow": self.rename,
                                     "blue": self.showContent}, -1)

        self.onLayoutFinish.append(self.showConfigs)

    def showConfigs(self):
        list = []

        try:
            files = listdir("/etc")
        except:
            files = []

        for file in files:
            if file.startswith("CCcam") and file.endswith(".cfg"):
                list.append(CCcamConfigListEntry("/etc/" + file))

        self["list"].setList(list)

    def delete(self):
        fileName = self["list"].getCurrent()
        if fileName is not None:
            self.fileToDelete = fileName[0]
            self.session.openWithCallback(self.deleteConfirmed, MessageBox, (_("Delete %s?") % self.fileToDelete))

    def deleteConfirmed(self, yesno):
        if yesno:
            remove(self.fileToDelete)
            if fileExists(self.fileToDelete):
                self.session.open(MessageBox, _("Delete failed!"), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _("Deleted %s!") % self.fileToDelete, MessageBox.TYPE_INFO)
                self.showConfigs()

    def activate(self):
        fileName = self["list"].getCurrent()
        if fileName is not None:
            fileName = fileName[0]
            # Delete old backup
            backupFile = "%s.backup" % CFG
            if fileExists(backupFile):
                remove(backupFile)
            # Create a backup of the original /var/etc/CCcam.cfg file
            rename(CFG, backupFile)
            # Now copy the selected cfg file
            system("cp -f %s %s" % (fileName, CFG))
            self.showConfigs()

    def rename(self):
        fileName = self["list"].getCurrent()
        if fileName is not None:
            self.fileToRename = fileName[0]
            (name, sel) = getConfigNameAndContent(self.fileToRename)
            self.session.openWithCallback(self.renameCallback, VirtualKeyBoard, title=_("Rename to:"), text=name)

    def renameCallback(self, callback):
        if callback is not None:
            try:
                f = open(self.fileToRename, "r")
                content = f.read()
                f.close()
            except:
                content = None

            if content is not None:
                content = content.replace("\r", "\n")
                if content.startswith("#CONFIGFILE NAME=") and content.__contains__("\n"):
                    idx = content.index("\n")
                    content = content[:idx + 2]

                content = "#CONFIGFILE NAME=%s\n%s" % (callback, content)

                try:
                    f = open(self.fileToRename, "w")
                    f.write(content)
                    f.close()
                    self.session.open(MessageBox, _("Renamed %s!") % self.fileToRename, MessageBox.TYPE_INFO)
                    self.showConfigs()
                except:
                    self.session.open(MessageBox, _("Rename failed!"), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _("Rename failed!"), MessageBox.TYPE_ERROR)

    def showContent(self):
        fileName = self["list"].getCurrent()
        if fileName is not None:
            try:
                f = open(fileName[0], "r")
                content = f.read()
                f.close()
            except:
                content = _("Could not open the file %s!") % fileName[0]
            self.session.open(CCcamInfoInfoScreen, content)


if width > 1280:
    CCcamInfoMenuConfig_SKIN = """
    <screen position="center,center" size="860,620" title="CCcam Info Config">
        <ePixmap pixmap="skin_default/buttons/red.png" position="20,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="235,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="445,0" size="180,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="655,0" size="180,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="20,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="235,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="445,0" zPosition="1" size="180,40" font="Regular;30" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="860,565" scrollbarMode="showOnDemand" />
    </screen>"""
else:
    CCcamInfoMenuConfig_SKIN = """
    <screen position="center,center" size="560,420" title="CCcam Info Config" >
        <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
        <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
        <widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
    </screen>"""


class CCcamInfoMenuConfig(Screen):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.skin = CCcamInfoMenuConfig_SKIN
        self.setTitle(_("CCcam Info Config"))
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["key_yellow"] = Label(_("Location"))
        self["list"] = CCcamConfigList([])
        self.getBlacklistedMenuEntries()

        self["actions"] = ActionMap(["CCcamInfoActions"],
                                    {"ok": self.changeState,
                                     "cancel": self.close,
                                     "red": self.close,
                                     "green": self.save,
                                     "yellow": self.location}, -1)

        self.onLayoutFinish.append(self.showConfigs)

    def getBlacklistedMenuEntries(self):
        try:
            f = open(config.plugins.CCcamInfo.blacklist.value, "r")
            content = f.read()
            f.close()
            self.blacklisted = content.split("\n")
        except:
            self.blacklisted = []

    def changeState(self):
        cur = self["list"].getCurrent()
        if cur is not None:
            cur = cur[0]
            if cur in self.blacklisted:
                idx = 0
                for x in self.blacklisted:
                    if x == cur:
                        del self.blacklisted[idx]
                        break
                    idx += 1
            else:
                self.blacklisted.append(cur)
        self.showConfigs()

    def showConfigs(self):
        list = []
        for x in menu_list:
            if x != _("Menu config"):
                if x in self.blacklisted:
                    list.append(CCcamMenuConfigListEntry(x, True))
                else:
                    list.append(CCcamMenuConfigListEntry(x, False))
        self["list"].setList(list)

    def save(self):
        content = ""
        for x in self.blacklisted:
            content = content + x + "\n"
        content = content.replace("\n\n", "\n")
        try:
            f = open(config.plugins.CCcamInfo.blacklist.value, "w")
            f.write(content)
            f.close()
            self.session.open(MessageBox, _("Configfile %s saved.") % config.plugins.CCcamInfo.blacklist.value, MessageBox.TYPE_INFO)
        except:
            self.session.open(MessageBox, _("Could not save configfile %s!") % config.plugins.CCcamInfo.blacklist.value, MessageBox.TYPE_ERROR)

    def location(self):
        self.session.openWithCallback(self.locationCallback, LocationBox)

    def locationCallback(self, callback):
        if callback:
            config.plugins.CCcamInfo.blacklist.value = ("%s/CCcamInfo.blacklisted" % callback).replace("//", "/")
            config.plugins.CCcamInfo.blacklist.save()


def main(session, **kwargs):
    session.open(CCcamInfoMain)


def sessionstart(reason, **kwargs):
    global ecmInfoStart
    if reason == 0 and ecmInfoStart is None:
        CCcamPrioMaker.CCPrioMakerAutostart(kwargs["session"])
        ecmInfoStart = ecmInfo.gotSession(kwargs["session"])


def openEcmInfoConfig(session, **kwargs):
    session.open(EcmInfoConfigMenu)


def startEcmInfoConfig(menuid):
    if menuid == "system" and config.plugins.CCcamInfo.ecmInfoMainMenu.value:
        return [(_("Ecm Info"), openEcmInfoConfig, "ecm_info", None)]
    return []


def Plugins(**kwargs):
    lst = [
        PluginDescriptor(name=_("CCcam Info %s") % VERSION, description=_("This plugin shows you the status of your CCcam"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="CCcamInfo.png", fnc=main),
        PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
        PluginDescriptor(name="Ecm Info", where=PluginDescriptor.WHERE_MENU, fnc=startEcmInfoConfig)]
    if config.plugins.CCcamInfo.showExtMenu.value:
        lst.append(PluginDescriptor(name=_("CCcam Info %s") % VERSION, description=_("This plugin shows you the status of your CCcam"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
    return lst

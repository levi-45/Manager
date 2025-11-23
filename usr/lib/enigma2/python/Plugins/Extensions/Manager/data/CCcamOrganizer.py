#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# CCam Organizer by fsenes 2011
# modded by lululla 20240314
from Screens.Screen import Screen
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists


class OrganizerMenu(Screen):
    skin = """
        <screen position="center,center" size="460,400" title="CCcam Organizer" >
            <widget name="myMenu" position="10,10" size="420,380" itemHeight="45" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        listx = []
        # if fileExists("/etc/CCcam.cfg"):
        listx.append((_("Delete Peer"), "two"))
        listx.append((_("Recover Peer"), "tree"))
        listx.append((_("Find Fakes"), "four"))
        listx.append((_("Stop Finding Fakes"), "five"))
        listx.append((_("Exit"), "exit"))
        self.setTitle(_("CCcam Organizer"))
        self["myMenu"] = MenuList(listx)
        self["actions"] = ActionMap(["SetupActions"], {"ok": self.go, "cancel": self.cancel}, -2)

    def go(self):
        if not fileExists("/etc/CCcam.cfg"):
            return
        global returnValue
        returnValue = self["myMenu"].l.getCurrentSelection() and self["myMenu"].l.getCurrentSelection()[1]
        # if returnValue is "five":
        if returnValue == "five":
            self.Revert()
        # elif returnValue is "exit":
        elif returnValue == "exit":
            self.close(None)
        else:
            self.session.open(OrganizerNewmenu)

    def cancel(self):
        self.close(None)

    def Revert(self):
        lines = []
        with open("/etc/CCcam.cfg", 'r') as f:
            for line in f:
                if line.startswith('#FC:'):
                    line = line.replace('#FC:', 'C:')
                lines.append(line)

        with open("/etc/CCcam.cfg", 'w') as f:
            for line in lines:
                f.write(line)

        self.session.open(MessageBox, _("\nSTOPPED FINDING FAKES \n\nREVERTED BACK TO INITIAL STATUS"), MessageBox.TYPE_INFO)


class OrganizerNewmenu(Screen):
    skin = """
        <screen position="center,center" size="460,400" title="CCcam Organizer" >
            <widget name="Newmenu" position="10,10" size="420,380" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.CFG = "/etc/CCcam.cfg"

        if not fileExists(self.CFG):
            self.close()
            return

        self.find = ""
        self.replace = ""
        self.selected = ""

        menu_list = []

        if returnValue == "two" or returnValue == "four":
            with open(self.CFG, 'r') as f:
                for line in f:
                    if line.startswith('C:') or line.startswith('C :'):
                        a = line.split()
                        if len(a) > 1:  # Ensure there is at least one argument
                            menu_list.append((_(a[1]), line))

        elif returnValue == "tree":
            with open(self.CFG, 'r') as f:
                for line in f:
                    if line.startswith('#!C:') or line.startswith('#!C :'):
                        a = line.split()
                        if len(a) > 1:  # Ensure there is at least one argument
                            menu_list.append((_(a[1]), line))
        self.setTitle(_("CCcam Organizer"))
        self["Newmenu"] = MenuList(menu_list)
        # if returnValue is "two":
        if returnValue == "two":
            self["Actions"] = ActionMap(["SetupActions"], {"ok": self.delete, "cancel": self.close}, -2)
        # elif returnValue is "tree":
        elif returnValue == "tree":
            self["Actions"] = ActionMap(["SetupActions"], {"ok": self.undelete, "cancel": self.close}, -2)
        # elif returnValue is "four":
        elif returnValue == "four":
            self["Actions"] = ActionMap(["SetupActions"], {"ok": self.FindFakes, "cancel": self.close}, -2)

    def delete(self):
        self.selected = self["Newmenu"].l.getCurrentSelection() and self["Newmenu"].l.getCurrentSelection()[1]
        if not self.selected:
            return
        self.findReplace("C:", "#!C:", self.selected)
        self.message(self.selected, _("Temporarely DELETED"))

    def undelete(self):
        if self["Newmenu"].l.getCurrentSelection() is not None:
            self.selected = self["Newmenu"].l.getCurrentSelection() and self["Newmenu"].l.getCurrentSelection()[1]
            if not self.selected:
                return
            self.findReplace("#!C:", "C:", self.selected)
            self.message(self.selected, _("UNDELETED"))
        else:
            self.selected = _("a NOTHING.TO.UNDELE")
            self.message(self.selected, _("PRESS RETURN"))

    def FindFakes(self):
        self.selected = self["Newmenu"].l.getCurrentSelection()
        self.selected = self.selected and self.selected[1]

        if not self.selected:
            return

        lines = []

        with open(self.CFG, 'r') as f:
            for line in f:
                if line.startswith("C:") and line.strip() != self.selected.strip():
                    line = line.replace("C:", "#FC:")
                lines.append(line)

        with open(self.CFG, 'w') as f:
            f.writelines(lines)

        self.message(self.selected, _("Set as UNIQUE PEER"))

    def findReplace(self, find, replace, selected):
        lines = []

        with open(self.CFG, 'r') as f:
            for line in f:
                if line.startswith(find) and selected in line:
                    line = line.replace(find, replace)
                lines.append(line)

        with open(self.CFG, 'w') as f:
            f.writelines(lines)

    def message(self, selected, text):
        try:
            msg = selected.split()[1]
            self.session.open(MessageBox, "\n%s \n\n%s" % (msg, text), MessageBox.TYPE_INFO)
        except:
            pass

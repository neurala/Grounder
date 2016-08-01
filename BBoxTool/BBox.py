# -------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ground truth data
# Author:      Qiushi
# Created:     06/06/2014
# Last updated by: Lucas Neves
# Last updated: 07/04/2016
#
# -------------------------------------------------------------------------------
from __future__ import division

from Tkinter import *

from VideoLabelTool import VideoLabelTool
from LabelTool import LabelTool
BASE = RAISED
SELECTED = FLAT

# image sizes for the examples
SIZE = 256, 256


class Tab(Frame):
    def __init__(self, master, name):
        Frame.__init__(self, master)
        self.tab_name = name


class TabBar(Frame):
    def __init__(self, master=None, init_name=None):
        Frame.__init__(self, master)
        self.tabs = {}
        self.buttons = {}
        self.current_tab = None
        self.init_name = init_name

    def show(self):
        self.pack(side=TOP, expand=YES, fill=X)
        self.switch_tab(self.init_name or self.tabs.keys()[-1])  # switch the tab to the first tab

    def add(self, tab):
        tab.pack_forget()  # hide the tab on init

        self.tabs[tab.tab_name] = tab  # add it to the list of tabs
        b = Button(self, text=tab.tab_name, relief=BASE,  # basic button stuff
                   command=(lambda name=tab.tab_name: self.switch_tab(name)))  # set the command to switch tabs
        b.pack(side=LEFT)  # pack the buttont to the left mose of self
        self.buttons[tab.tab_name] = b  # add it to the list of buttons

    def delete(self, tabname):

        if tabname == self.current_tab:
            self.current_tab = None
            self.tabs[tabname].pack_forget()
            del self.tabs[tabname]
            self.switch_tab(self.tabs.keys()[0])

        else:
            del self.tabs[tabname]

        self.buttons[tabname].pack_forget()
        del self.buttons[tabname]

    def switch_tab(self, name):
        if self.current_tab:
            self.buttons[self.current_tab].config(relief=BASE)
            self.tabs[self.current_tab].pack_forget()  # hide the current tab
        self.tabs[name].pack(side=BOTTOM)  # add the new tab to the display
        self.current_tab = name  # set the current tab to itself

        self.buttons[name].config(relief=SELECTED)  # set it to the selected style


if __name__ == '__main__':
    root = Tk()
    root.title("Tabs")
    bar = TabBar(root, "Image Grounding")
    tab1 = Tab(root, "Video Grounding")
    videoground = VideoLabelTool(tab1, "Video Grounding")
    tab2 = Tab(root, "Image Grounding")
    photoground = LabelTool(tab2, "Image Grounding")
    bar.add(tab1)
    bar.add(tab2)
    bar.show()
    root.mainloop()

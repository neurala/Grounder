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
import os
from Tkinter import *
import tkFileDialog as filedialog
import xml.etree.ElementTree as ET  # for xml output
import glob
from PIL import Image, ImageTk
import cv2
import neurala

COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

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


class LabelTool(Frame):
    def __init__(self, master, name):
        Frame.__init__(self, master)
        self.tab_name = name
        # set up the main frame
        self.parent = master
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.tree = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        # dir entry & load
        self.ldBtn = Button(self.frame, text="Load File", command=self.loadDir)  # command
        self.ldBtn.grid(row=0, column=1, sticky=W + E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)

        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.mainPanel.grid(row=1, column=1, rowspan=5, sticky=W + N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=1, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=2, column=2, sticky=N)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=3, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='ClearAll', command=self.clearBBox)
        self.btnClear.grid(row=4, column=2, sticky=W + E + N)

        # bbox label and save
        self.labelentry = Entry(self.frame)
        self.labelentry.grid(row=5, column=2, sticky=W + E)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=6, column=1, columnspan=2, sticky=W + E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.gotoImage)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

        self.parent.bind("<Left>", self.prevImage)
        self.parent.bind("<Right>", self.nextImage)

    def loadDir(self, dbg=False):

        if not dbg:
            folderPath = filedialog.askdirectory()
        else:
            s = r'D:\workspace\python\labelGUI'

        # get image list
        self.imageDir = folderPath
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print 'No .JPEG images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
        # set up output dir
        self.outDir = os.path.join(r'./Labels', '%s' % (os.path.basename(folderPath)))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.loadImage()
        print '%d images loaded from %s' % (self.total, os.path.basename(folderPath))

    def readxml(self):
        self.tree = ET.parse(self.labelfilename)
        treeroot = self.tree.getroot()
        frames = treeroot.find('frames')
        frame = frames.find('frame')
        for objects in frame.findall('object'):
            point = objects.find('point')
            x1 = int(point.get('x1_coord'))
            x2 = int(point.get('x2_coord'))
            y1 = int(point.get('y1_coord'))
            y2 = int(point.get('y2_coord'))
            name = objects.get('id')
            self.bboxList.append((x1, y1, x2, y2, name))
            tmpId = self.mainPanel.create_rectangle(x1, y1, \
                                                    x2, y2, \
                                                    width=2, \
                                                    outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
            self.bboxIdList.append(tmpId)
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, name))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.xml'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            self.readxml()
        else:  # create xml file if it does not exist
            self.newxml()
            print 'created new xml!'
            print self.tree

    def newxml(self):
        rootelement = ET.Element('doc')
        parameters = ET.SubElement(rootelement, 'parameters')
        res = ET.SubElement(parameters, 'resolution')
        width, height = self.img.size
        res.set('x_res', str(width))
        res.set('y_res', str(height))
        multipoint = ET.SubElement(parameters, 'multipoint')
        multipoint.set('attribute', 'False')  # this tool does not support polygons yet
        # skip fov,object values, and framerate
        # set up frames section
        frames = ET.SubElement(rootelement, 'frames')
        frame = ET.SubElement(frames, 'frame')
        frame.set('index', '0')
        # basic XML structure set up, lets bind to the tree and begin
        self.tree = ET.ElementTree(rootelement)

    def saveImage(self):
        if self.tree != None:
            self.tree.write(self.labelfilename)

        print 'Image No. %d saved' % (self.cur)

    def addxmlnode(self, x1, y1, x2, y2, label, idx):
        xmlroot = self.tree.getroot()

        frames = xmlroot.find('frames')
        frame = frames.find('frame')  # only works for single frame data
        print frame
        newobject = ET.SubElement(frame, 'object')
        newobject.set('id', label)
        newobject.set('idx', str(idx))
        rect = ET.SubElement(newobject, 'point')
        rect.set('x1_coord', str(x1))
        rect.set('y1_coord', str(y1))
        rect.set('x2_coord', str(x2))
        rect.set('y2_coord', str(y2))

    def remxmlnode(self, idx):
        xmlroot = self.tree.getroot()
        frames = xmlroot.find('frames')
        frame = frames.find('frame')

        for objects in frame.findall('object'):
            if objects.get('idx') == str(idx):
                frame.remove(objects)

        allobjects = frame.findall('object')
        for i in range(0, len(frame.findall('object'))):
            allobjects[i].set('idx', str(i))

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            label = self.labelentry.get()
            self.bboxIdList.append(self.bboxId)
            idx = len(self.bboxIdList) - 1
            self.bboxList.append((x1, y1, x2, y2, label, idx))
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, label))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            self.addxmlnode(x1, y1, x2, y2, label, idx)

        self.STATE['click'] = 1 - self.STATE['click']
        self.parent.focus_set()

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                          event.x, event.y, \
                                                          width=2, \
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.remxmlnode(idx)
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        if (self.tree != None):
            xmlroot = self.tree.getroot()
            frames = xmlroot.find('frames')
            frame = frames.find('frame')
            for objects in frame.findall('object'):
                frame.remove(objects)

        for idx in range(len(self.bboxIdList)):
            self.remxmlnode(idx)
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event=None):
        self.saveImage()  # make this switch xml contexts
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event=None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()


class VideoLabelTool(Frame):  # need tracker to complete this bit
    def __init__(self, master, name):
        Frame.__init__(self, master)
        self.tab_name = name
        # set up the main frame
        self.xmlinit = True
        self.xmlframes = None
        self.currentFrame = None

        self.parent = master
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.outDir = ""
        self.labelfilename = ""
        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.ldBtn = Button(self.frame, text="Load File", command=self.loadFile)  # command
        self.ldBtn.grid(row=0, column=1, sticky=W + E)

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None
        self.tree = None

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, bd=0, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Escape> to cancel current bbox self.cancelBBox
        self.mainPanel.config(scrollregion=self.mainPanel.bbox(ALL))
        self.scale = 1.0
        self.orig_img = None
        self.img = None
        self.img_id = None
        self.mainPanel.bind("<Button 3>", self.grab)
        self.mainPanel.bind("<B3-Motion>", self.drag)
        self.mainPanel.bind("<Button-4>", self.zoom)
        self.mainPanel.bind("<Button-5>", self.zoom)

        self.mainPanel.grid(row=1, column=1, rowspan=8, sticky=N+S+E+W)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=1, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=2, column=2, sticky=N)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=3, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='Clear All', command=self.clearBBox)
        self.btnClear.grid(row=4, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='autoloop', command=self.loopToggle)
        self.btnClear.grid(row=5, column=2, sticky=W + E + N)
        self.btnReset = Button(self.frame, text='Reset Trackers', command=self.resetTrackers)
        self.btnReset.grid(row=6, column=2, sticky=W + E + N)
        self.btninit = Button(self.frame, text='new Tracker', command=self.initTrackers)
        self.btninit.grid(row=7, column=2, sticky=W + E + N)
        self.btnrem = Button(self.frame, text='remove Trackers', command=self.remTrackers)
        self.btnrem.grid(row=8, column=2, sticky=W + E + N)


        # bbox label and save
        self.labelentry = Entry(self.frame)
        self.labelentry.grid(row=9, column=2, sticky=W + E)
        self.lablepanel = Frame(self.frame)
        self.lablepanel.grid(row=9, column=1, columnspan=1, sticky=W + E)
        self.label = Label(self.lablepanel, text="Label:")
        self.label.pack(side=RIGHT, padx=5, pady=3)
        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=10, column=1, columnspan=2, sticky=W + E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command=self.prevFrame)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command=self.nextFrame)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Frame No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.gotoFrame)
        self.goBtn.pack(side=LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)
        self.total = 0
        self.video = None
        self.tree = None
        self.videoFilePath = ""
        self.videoFile = ""
        self.cur = 0
        self.tkimg = None

        # these need to work
        self.parent.bind("<Left>", self.prevFrame)
        self.parent.bind("<Right>", self.nextFrame)
        self.parent.bind("<Delete>", self.clearBBox)

        self.trackers = []
        self.videoinput = None
        self.parent.focus_set()
        self.currentImage = None
        self.doLoop = False
        self.jobid = None
        self.scaleimg = None
        self.trackerInit = False
        self.xoffset=0.0
        self.yoffset=0.0

    def grab(self, event):
        self._y = event.y
        self._x = event.x

    def drag(self, event):

        if (self._y-event.y < 0):
            self.yoffset += 10
            self.mainPanel.move(ALL, 0, 10)
        elif (self._y-event.y > 0):
            self.yoffset -= 10
            self.mainPanel.move(ALL, 0, -10)
        if (self._x-event.x < 0):
            self.xoffset += 10
            self.mainPanel.move(ALL, 10, 0)
        elif (self._x-event.x > 0):
            self.xoffset -= 10
            self.mainPanel.move(ALL, -10, 0)

        if self.img_id:
            self.mainPanel.delete(self.img_id)

        self.img_id = self.mainPanel.create_image(self.xoffset, self.yoffset, image=self.img, anchor=NW)
        self.mainPanel.tag_lower(self.img_id)

        self._x = event.x
        self._y = event.y

    def zoom(self, event):

        self.mainPanel.move(ALL, -self.xoffset, -self.yoffset)
        if event.num == 4:
            self.scale *= 2
            self.mainPanel.scale(ALL, 0, 0, 2, 2)
        elif event.num == 5:
            self.scale *= 0.5
            self.mainPanel.scale(ALL, 0, 0, 0.5, 0.5)

        self.redraw()

    def redraw(self, x=0, y=0):
        if self.img_id:
            self.mainPanel.delete(self.img_id)
        iw, ih = self.orig_img.size
        print iw
        print ih
        print self.scale
        size = int(iw * self.scale), int(ih * self.scale)
        print size
        self.img = ImageTk.PhotoImage(image=self.orig_img.resize(size))

        self.img_id = self.mainPanel.create_image(x, y, image=self.img, anchor=NW)
        self.mainPanel.tag_lower(self.img_id)
        self.mainPanel.move(ALL, self.xoffset, self.yoffset)


    def remTrackers(self):
        self.trackers = []
    def loadFile(self, dbg=False):
        self.videoFilePath = filedialog.askopenfilename()
        self.videoFile = os.path.basename(self.videoFilePath)
        self.videoinput = neurala.NEUVideoInput(self.videoFilePath, 0)
        self.videoinput.scale(1.0)
        self.videoinput.nextFrame()
        print self.videoinput.frameNumber()
        # set up output dir
        self.outDir = os.path.dirname(self.videoFilePath)
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        self.video = cv2.VideoCapture(self.videoFilePath)
        self.total = int(self.video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))

        videoname = os.path.split(self.videoFilePath)[-1].split('.')[0]
        labelname = videoname + '.xml'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0

        if os.path.exists(self.labelfilename):
            self.readxml()
            print 'reading xml from %s' % (self.labelfilename)

        else:  # create xml file if it does not exist
            self.newxml()
            print 'created new xml!'
            print self.tree
        self.loadVideo()
        print '%d frames of video loaded from %s' % (self.total, self.videoFilePath)
        print 'xml loaded from %s' % (self.labelfilename)

    def readxml(self):
        if self.xmlinit:
            self.tree = ET.parse(self.labelfilename)
            treeroot = self.tree.getroot()
            self.xmlframes = treeroot.find('frames')
            self.xmlinit = False

        self.currentFrame = self.xmlframes.find('./frame[@index="' + str(self.cur) + '"]')
        if self.currentFrame == None:
            self.newXmlFrame()
        for objects in self.currentFrame.findall('object'):
            point = objects.find('point')
            x1 = int(point.get('x1_coord'))
            x2 = int(point.get('x2_coord'))
            y1 = int(point.get('y1_coord'))
            y2 = int(point.get('y2_coord'))
            name = objects.get('id')
            self.bboxList.append((x1, y1, x2, y2, name))
            tmpId = self.mainPanel.create_rectangle((x1 * self.scale) + self.xoffset, (y1 * self.scale) + self.yoffset,
                                                    (x2 * self.scale) + self.xoffset, (y2 * self.scale) + self.yoffset,
                                                    width=2,
                                                    outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
            self.bboxIdList.append(tmpId)
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, name))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def newTracker(self, x1, y1, x2, y2, label, idx):
        tracker = neurala.Tracker(self.videoinput, 0.8, 3.0, 0)
        width = self.videoinput.width()
        height = self.videoinput.height()
        x1f = float(x1/width)
        y1f = float(y1/height)
        x2f = float(x2/width)
        y2f = float(y2/height)
        result = tracker.startTracker(x1f, y1f, x2f, y2f)
        self.trackers.append((tracker, label, idx))

    def loadVideo(self):
        ret, videoframe =self.video.read()
        cv2image = cv2.cvtColor(videoframe, cv2.COLOR_BGR2RGBA)

        img = Image.fromarray(cv2image)
        self.orig_img= img
        self.tkimg = ImageTk.PhotoImage(image=img)
        if self.currentImage != None:
            self.mainPanel.delete(self.currentImage)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
     #   self.currentImage = self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))
        self.reset()
        self.redraw()
        self.readxml()


    def newXmlFrame(self):
        newxmlframe = ET.SubElement(self.xmlframes, 'frame')
        newxmlframe.set('index', str(self.cur))
        self.currentFrame = newxmlframe

    def newxml(self):
        rootelement = ET.Element('doc')
        parameters = ET.SubElement(rootelement, 'parameters')
        res = ET.SubElement(parameters, 'resolution')
        width = self.videoinput.width()
        height = self.videoinput.height()
        res.set('x_res', str(width))
        res.set('y_res', str(height))
        multipoint = ET.SubElement(parameters, 'multipoint')
        multipoint.set('attribute', 'False')  # this tool does not support polygons yet
        # skip fov,object values,
        framerate = ET.SubElement(parameters, 'framerate')
        fps = self.video.get(cv2.cv.CV_CAP_PROP_FPS)
        framerate.set('rate', str(fps))
        # set up frames section
        frames = ET.SubElement(rootelement, 'frames')
        frame = ET.SubElement(frames, 'frame')
        frame.set('index', '0')  # set first frame
        self.currentFrame = frame
        # basic XML structure set up, lets bind to the tree and begin
        self.tree = ET.ElementTree(rootelement)
        self.saveFrame()

    def saveFrame(self):
        if self.tree != None:
            self.tree.write(self.labelfilename)

        print 'Image No. %d saved' % (self.cur)

    def addxmlnode(self, x1, y1, x2, y2, label, idx):

        newobject = ET.SubElement(self.currentFrame, 'object')
        newobject.set('id', label)
        newobject.set('idx', str(idx))
        rect = ET.SubElement(newobject, 'point')
        rect.set('x1_coord', str(x1))
        rect.set('y1_coord', str(y1))
        rect.set('x2_coord', str(x2))
        rect.set('y2_coord', str(y2))

    def remxmlnode(self, idx):

        for objects in self.currentFrame.findall('object'):
            if objects.get('idx') == str(idx):
                self.currentFrame.remove(objects)

        allobjects = self.currentFrame.findall('object')
        for i in range(0, len(allobjects)):
            allobjects[i].set('idx', str(i))

    def initTrackers(self):
        self.trackerInit = True

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            x1 -= self.xoffset
            x2 -= self.xoffset
            y1 -= self.yoffset
            y2 -= self.yoffset
            x1 /= self.scale
            x2 /= self.scale
            y1 /= self.scale
            y2 /= self.scale
            label = self.labelentry.get()
            self.bboxIdList.append(self.bboxId)
            idx = len(self.bboxIdList) - 1
            self.bboxList.append((x1, y1, x2, y2, label, idx))
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, label))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            self.addxmlnode(int(x1), int(y1), int(x2), int(y2), label, idx)
            if(self.trackerInit):
                self.newTracker(x1, y1, x2, y2, label, idx)

        self.STATE['click'] = 1 - self.STATE['click']
        self.parent.focus_set()

    def mouseMove(self, event):
        self.disp.config(text='x: %d, y: %d' % (event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                          event.x, event.y, \
                                                          width=2, \
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.remxmlnode(idx)
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self, event=None):
        if self.currentFrame != None:
            for objects in self.currentFrame.findall('object'):
                self.currentFrame.remove(objects)

        for idx in range(len(self.bboxIdList)):
            self.remxmlnode(idx)
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def reset(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevFrame(self, event=None):
        self.saveFrame()
        if self.trackerInit:
            self.trackerInit = False
        if self.cur > 0:
            self.cur -= 1
            self.videoinput.frameNumber(self.cur)
            self.video.set(1, self.cur)
            self.loadVideo()

    def nextFrame(self, event=None):
        self.saveFrame()
        if self.trackerInit:
            self.trackerInit = False

        if self.cur < self.total-1:
            self.videoinput.nextFrame()
            self.cur += 1
            self.loadVideo()
            if len(self.currentFrame.findall('object')) == 0:
                #prevframe = self.xmlframes.find('./frame[@index="' + str(self.cur - 1) + '"]')
                if len(self.trackers) >0:
                    for elements in self.trackers:
                        bbox = elements[0].trackFrame()
                        x1 = int(bbox[1])
                        y2 = int(bbox[2])
                        x2 = int(bbox[3])
                        y1 = int(bbox[4])
                        name = elements[1]
                        idx = elements[2]
                        self.bboxList.append((x1, y1, x2, y2, name))
                        tmpId = self.mainPanel.create_rectangle((x1*self.scale)+self.xoffset, (y1*self.scale)+self.yoffset, \
                                                                (x2*self.scale)+self.xoffset, (y2*self.scale)+self.yoffset, \
                                                                width=2, \
                                                                outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
                        self.bboxIdList.append(tmpId)
                        self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, name))
                        self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                                fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
                        self.addxmlnode(x1, y1, x2, y2, name, idx)
        print self.videoinput.frameNumber()

    def gotoFrame(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveFrame()
            self.cur = idx
            self.video.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0.0)
            count = 0
            while count != self.cur:
                self.video.read()
                count += 1
            self.loadVideo()

    def resetTrackers(self, event=None):
        width = self.videoinput.width()
        height = self.videoinput.height()

        for bbox in self.bboxList:
            for tracker in self.trackers:
                if bbox[4] == tracker[1]:
                    x1f = float(bbox[0] / width)
                    y1f = float(bbox[1] / height)
                    x2f = float(bbox[2] / width)
                    y2f = float(bbox[3] / height)
                    tracker[0].startTracker(x1f, y1f, x2f, y2f)

    def loopToggle(self, event=None):
        if self.doLoop:
            self.doLoop = False
            root.after_cancel(self.jobid)
        else:
            self.doLoop = True
            self.loopnext()

        print "got loop command"

    def loopnext(self, event=None):
        if self.doLoop:
            self.nextFrame()
            self.jobid = root.after(10, self.loopnext)

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

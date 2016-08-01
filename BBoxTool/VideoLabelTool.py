import os
from Tkinter import *
import cv2
import neurala
import tkFileDialog as filedialog
import xml.etree.ElementTree as ET  # for xml output
from PIL import Image, ImageTk

COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']


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
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Escape> to cancel current bbox self.cancelBBox
        self.mainPanel.grid(row=1, column=1, rowspan=5, sticky=W + N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=1, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width=22, height=12)
        self.listbox.grid(row=2, column=2, sticky=N)
        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=3, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='Clear All', command=self.clearBBox)
        self.btnClear.grid(row=4, column=2, sticky=W + E + N)
        self.btnReset = Button(self.frame, text='Reset Trackers', command=self.resetTrackers)
        self.btnReset.grid(row=5, column=2, sticky=W + E + N)

        # bbox label and save
        self.labelentry = Entry(self.frame)
        self.labelentry.grid(row=6, column=2, sticky=W + E)
        self.lablepanel = Frame(self.frame)
        self.lablepanel.grid(row=6, column=1, columnspan=1, sticky=W + E)
        self.label = Label(self.lablepanel, text="Label:")
        self.label.pack(side=RIGHT, padx=5, pady=3)
        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=7, column=1, columnspan=2, sticky=W + E)
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

        self.labelentry.bind("<Left>", self.prevFrame)
        self.labelentry.bind("<Right>", self.nextFrame)
        self.labelentry.bind("<Delete>", self.clearBBox)
        self.trackers = []
        self.videoinput = None
        self.parent.focus_set()

    def loadFile(self, dbg=False):
        self.videoFilePath = filedialog.askopenfilename()
        self.videoFile = os.path.basename(self.videoFilePath)
        self.videoinput = neurala.neuVideoInput(self.videoFilePath, 0)
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
            tmpId = self.mainPanel.create_rectangle(x1, y1, \
                                                    x2, y2, \
                                                    width=2, \
                                                    outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
            self.bboxIdList.append(tmpId)
            self.listbox.insert(END, '(%d, %d) -> (%d, %d) %s' % (x1, y1, x2, y2, name))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def newTracker(self, x1, y1, x2, y2, label, idx):
        tracker = neurala.Tracker(self.videoinput, 0.8, 3.0, 1)
        width = self.videoinput.width()
        height = self.videoinput.height()
        x1f = float(x1/width)
        y1f = float(y1/height)
        x2f = float(x2/width)
        y2f = float(y2/height)
        result = tracker.startTracker(x1f, y1f, x2f, y2f)
        self.trackers.append((tracker, label, idx))

    def loadVideo(self):

        ret, videoframe = self.video.read()
        cv2image = cv2.cvtColor(videoframe, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        self.tkimg = ImageTk.PhotoImage(image=img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))
        self.reset()
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
            if(self.cur ==0):
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
        if self.cur > 0:
            self.cur -= 1
            self.videoinput.frameNumber(self.cur+1)
            self.video.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0.0)
            count = 0
            while count != self.cur:
                self.video.read()
                count += 1
            self.loadVideo()

    def nextFrame(self, event=None):
        self.saveFrame()

        if self.cur < self.total-1:
            self.videoinput.nextFrame()
            self.cur += 1
            self.loadVideo()
            if len(self.currentFrame.findall('object')) == 0:
                #prevframe = self.xmlframes.find('./frame[@index="' + str(self.cur - 1) + '"]')

                width = self.tkimg.width()
                height = self.tkimg.height()
                for elements in self.trackers:
                    bbox = elements[0].trackFrame()
                    x1 = int(bbox[1])
                    y2 = int(bbox[2])
                    x2 = int(bbox[3])
                    y1 = int(bbox[4])
                    name = elements[1]
                    idx = elements[2]
                    self.bboxList.append((x1, y1, x2, y2, name))
                    tmpId = self.mainPanel.create_rectangle(x1, y1, \
                                                            x2, y2, \
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

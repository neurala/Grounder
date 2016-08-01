import os
from Tkinter import *
import tkFileDialog as filedialog
import xml.etree.ElementTree as ET  # for xml output
import glob
from PIL import Image, ImageTk

COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

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
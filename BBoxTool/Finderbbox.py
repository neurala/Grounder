#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ground truth data
# Author:      Qiushi
# Created:     06/06/2014
# Last updated by: Lucas Neves
# Last updated: 07/04/2016
#
#-------------------------------------------------------------------------------
from __future__ import division

from Tkinter import *
import tkFileDialog as filedialog
from PIL import Image, ImageTk
import os
import glob
import csv
import cv2

BASE = RAISED
SELECTED = FLAT

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black'] #max of 7 classes for now
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=True)
        self.parent.resizable(width = True, height = True)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.classlist = []

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
        self.ldBtn = Button(self.frame, text="Load Directory", command=self.loadDir)  # command
        self.ldBtn.grid(row=5, column=2, sticky=W + E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, bd=0, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Escape> to cancel current bbox self.cancelBBox
        self.parent.bind("<Key>", self.selectLabel)
        self.mainPanel.config(scrollregion=self.mainPanel.bbox(ALL))
        self.scale = 1.0
        self.orig_img = None
        self.img = None
        self.img_id = None
        self.mainPanel.bind("<Button-4>", self.zoom)
        self.mainPanel.bind("<Button-5>", self.zoom)

        self.mainPanel.grid(row=1, column=1, rowspan=8, sticky=N+W)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 4, column = 2, sticky = W+E+N)

        #bbox label and save
        self.labelentry = Button(self.frame, text= 'define classes', command = self.classdefine)
        self.labelentry.grid(row=6, column=2, sticky=W + E)
        self.labelentry.config(state = DISABLED)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        self.xoffset=0.0
        self.yoffset=0.0
        self.scaleimg = None
        self.currentImage = None
        self.currentLabel = 0
        self.parent.focus_set()
        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        self.parent.bind("<Left>", self.prevImage)
        self.parent.bind("<Right>", self.nextImage)
        self.top = None

    def selectLabel(self, event):

        if event.char == "1":
            self.currentLabel = 0
        elif event.char == "2":
            self.currentLabel = 1
        elif event.char == "3":
            self.currentLabel = 2
        elif event.char == "4":
            self.currentLabel = 3
        elif event.char == "5":
            self.currentLabel = 4
        elif event.char == "6":
            self.currentLabel = 5
        elif event.char == "7":
            self.currentLabel = 6

    def loadDir(self, dbg=False):

        folderPath = filedialog.askdirectory()

        # get image list
        self.imageDir = folderPath
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print 'No jpeg images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
         # set up output dir
        self.outDir = os.path.join(r'%s' %(self.imageDir),'Labels', )
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
        self.classlist = []
        self.loadImage()
        self.labelentry.config(state=NORMAL)
        print '%d images loaded from %s' %(self.total, os.path.basename(folderPath))
        print ' Annotations will be saved to: %s' %(self.outDir)

    def readfile(self): #use  plaintext parsing
        # load labels
        self.clearBBox()
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename,'r') as f:
                reader = csv.reader(f, delimiter=" ")
                for row in reader:
                    print str(self.tkimg.width())
                    self.bboxList.append(row)
                    x1 = int(float(row[1])* self.tkimg.width())
                    y1 = int(float(row[2])* self.tkimg.height())
                    x2 =int(float(row[3])* self.tkimg.width())
                    y2 = int(float(row[4])* self.tkimg.height())
                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=COLORS[int(row[0])])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%f, %f) -> (%f, %f)' % (float(row[1]), float(row[2]), float(row[3]), float(row[4])))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[int(row[0])])
                self.mainPanel.scale(ALL, 0, 0, self.scale, self.scale)
                self.redraw()

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]

        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.orig_img = self.img
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))


        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            self.readfile()

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            for bbox in self.bboxList:
                for element in bbox:
                    print element
                    f.write(str(element))
                    f.write(' ')
                f.write('\n')
            f.close()
        print 'Image No. %d saved to %s' % (self.cur, self.labelfilename)
    def grab(self, event):
        self._y = event.y
        self._x = event.x

    def drag(self, event):

        if (self._y - event.y < 0):
            self.yoffset += 10
            self.mainPanel.move(ALL, 0, 10)
        elif (self._y - event.y > 0):
            self.yoffset -= 10
            self.mainPanel.move(ALL, 0, -10)
        if (self._x - event.x < 0):
            self.xoffset += 10
            self.mainPanel.move(ALL, 10, 0)
        elif (self._x - event.x > 0):
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
        self.tkimg = ImageTk.PhotoImage(image=self.orig_img.resize(size))

        self.img_id = self.mainPanel.create_image(x, y, image=self.tkimg, anchor=NW)
        self.mainPanel.tag_lower(self.img_id)
        self.mainPanel.move(ALL, self.xoffset, self.yoffset)

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            # x1 -= self.xoffset
            # x2 -= self.xoffset
            # y1 -= self.yoffset
            # y2 -= self.yoffset
            # x1 /= self.scale
            # x2 /= self.scale
            # y1 /= self.scale
            # y2 /= self.scale
            self.bboxIdList.append(self.bboxId)
            self.bboxList.append((self.currentLabel, float(x1/self.tkimg.width()), float(y1/self.tkimg.height()), float(x2/self.tkimg.width()), float(y2/self.tkimg.height())))
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' % (x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[self.currentLabel])

        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[self.currentLabel])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage() #make this switch xml contexts
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
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
    def classdefine(self):
        self.top = Toplevel()
        self.top.title("Define Classes")

        lbl1 = Entry(self.top)
        lbl1.grid(row=1, column=2, sticky=W + E)
        self.classlist.append(lbl1)
        name1 = Label(self.top,text="class 1:")
        name1.grid(row=1, column=1, sticky=W + E)
        lbl2 = Entry(self.top)
        lbl2.grid(row=2, column=2, sticky=W + E)
        self.classlist.append(lbl2)
        name2 = Label(self.top,text="class 2:")
        name2.grid(row=2, column=1, sticky=W + E)
        lbl3 = Entry(self.top)
        lbl3.grid(row=3, column=2, sticky=W + E)
        self.classlist.append(lbl3)
        name3 = Label(self.top,text="class 3:")
        name3.grid(row=3, column=1, sticky=W + E)
        lbl4 = Entry(self.top)
        lbl4.grid(row=4, column=2, sticky=W + E)
        self.classlist.append(lbl4)
        name4 = Label(self.top,text="class 4:")
        name4.grid(row=4, column=1, sticky=W + E)
        lbl5 = Entry(self.top)
        lbl5.grid(row=5, column=2, sticky=W + E)
        self.classlist.append(lbl5)
        name5 = Label(self.top,text="class 5:")
        name5.grid(row=5, column=1, sticky=W + E)
        lbl6 = Entry(self.top)
        lbl6.grid(row=6, column=2, sticky=W + E)
        self.classlist.append(lbl6)
        name6 = Label(self.top,text="class 6:")
        name6.grid(row=6, column=1, sticky=W + E)
        lbl7 = Entry(self.top)
        lbl7.grid(row=7, column=2, sticky=W + E)
        self.classlist.append(lbl7)
        name7 = Label(self.top,text="class 7:")
        name7.grid(row=7, column=1, sticky=W + E)

        button = Button(self.top, text="Save", command=self.createlabels)
        button.grid(row=8,column=2, sticky=N+S+E+W)
    def createlabels(self):
        labelfile = os.path.join(self.outDir, "labels.txt")
        with open(labelfile, 'w') as f:
            for labels in self.classlist:
                f.write(str(labels.get()))
                f.write('\n')
            f.close()
        self.top.destroy()

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()

from __future__ import division

from Tkinter import *
import tkFileDialog as filedialog
from PIL import Image, ImageTk
import cv2
import time
import os
import glob
import csv
import subprocess
#import ResizingCanvas

BASE = RAISED
SELECTED = FLAT
COLORS = ['red', 'peru', 'DarkOrange1', 'green', 'green3', 'DarkSlateGray4', 'blue', 'cyan', 'orchid1', 'maroon4'] #max of 10 classes for now
# image sizes for the examples
SIZE = 256, 256

class mainwindow():
    def __init__(self, master):
        self.parent = master
        self.frame = Toplevel()

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(14, weight = 1)

        self.tkimg = None

        self.frame.protocol('WM_DELETE_WINDOW', self.doSomething)  # root is your root window

        self.scale = 1.0

        self.orig_img = None
        self.img_id = None

        #zoom and pan positional data
        self.xoffset = 0.0
        self.yoffset = 0.0
        self._y = 0.0
        self._x = 0.0
        self.scaleimg = None
        self.currentImage = None

        self.hl = None
        self.vl = None
        self.bboxId = None


        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0
        # ----------------- GUI stuff ---------------------

        # main panel for labeling
        self.outerFrame = Frame(self.frame)
        self.outerFrame.pack(fill="both",expand=True)

        self.mainPanel = Canvas(self.outerFrame,width=400, height=400, bd=0, cursor='tcross')
        self.mainPanel.pack(fill="both", expand=True)


        self.ctrPanel = Frame(self.outerFrame)
        self.ctrPanel.pack(fill="both", expand=True)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)


        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.idxEntry.config(bg='white')
        self.goBtn = Button(self.ctrPanel, text='Go', state=DISABLED, command = self.parent.gotoImage)
        self.goBtn.pack(side = LEFT)
        self.resetBtn = Button(self.ctrPanel, text= 'reset view', command = self.resetView)
        self.resetBtn.pack(side = LEFT)
        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)
        self.initW=0.0
        self.inith=0.0

        self.splash()

    def resizeWindow(self, event):
        self.mainPanel.config( width = max(event.width-4,self.initW), height = max(event.height-4,self.inith))

    def splash(self):
        raw_img = Image.open("./Images/001/splash.jpg") #SPLASH SCREEN SOURCE GOES HERE
        self.tkimg = ImageTk.PhotoImage(raw_img)
        self.initW = self.tkimg.width()
        self.inith = self.tkimg.height()
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.mainPanel.bind('<Configure>', self.resizeWindow)
        self.frame.update()
        self.frame.minsize(width=self.initW, height=self.inith+30)

    def bindInterface(self):
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<ButtonRelease-1>", self.mouseRelease)
        self.mainPanel.bind("<Button-2>", self.grab)
        self.mainPanel.bind("<B3-Motion>", self.drag)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.mainPanel.bind("<Escape>", self.cancelBBox)  # press <Escape> to cancel current bbox self.cancelBBox
        self.mainPanel.bind("<Key>", self.hotkeys)
        self.mainPanel.config(scrollregion=self.mainPanel.bbox(ALL))

        self.mainPanel.bind("<Button-4>", self.zoom)
        self.mainPanel.bind("<Button-5>", self.zoom)

        self.mainPanel.bind("<Left>", self.parent.prevImage)
        self.mainPanel.bind("<Right>", self.parent.nextImage)
        self.mainPanel.bind("<MouseWheel>", self.zoom)
        self.goBtn.config(state=NORMAL)

    def mouseRelease(self,event):
        if self.STATE['click'] == 1:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            x1 = x1 - self.xoffset
            x2 = x2 - self.xoffset
            y1 = y1 - self.yoffset
            y2 = y2 - self.yoffset

            self.mainPanel.itemconfig(self.bboxId, dash=(2,2))


            Floatvals =[]
            Floatvals.append(float(x1 / self.tkimg.width()))
            Floatvals.append(float(y1 / self.tkimg.height()))
            Floatvals.append(float(x2 / self.tkimg.width()))
            Floatvals.append(float(y2 / self.tkimg.height()))
            for i in range(0,len(Floatvals)):
                if Floatvals[i] > 1.0:
                    self.cancelBBox(event)
                    print "box out of bounds!!!"
                    return
                elif Floatvals[i] < 0.0:
                    self.cancelBBox(event)
                    print "box out of bounds!!!"
                    return

            self.parent.bboxIdList.append(self.bboxId)
            width= Floatvals[2]-Floatvals[0] #x2-x1
            height= Floatvals[3]-Floatvals[1] #y2-y1
            centerx = Floatvals[0]+(width/2.0) #x1+w/2
            centery = Floatvals[1]+(height/2.0) #y1+h/2

            self.parent.bboxList.append((self.parent.currentLabel, centerx, centery, width, height))
            self.bboxId = None
            self.parent.listbox.insert(END, '(%f, %f) -> (%f, %f)' % (centerx, centery, width, height)) #need to set precision here
            self.parent.listbox.itemconfig(len(self.parent.bboxIdList) - 1, fg=COLORS[self.parent.currentLabel])
            self.STATE['click']=0

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
            self.STATE['click'] =1

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        self.mainPanel.focus_set()
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
                                                            outline = COLORS[self.parent.currentLabel],dash=(2, 4))
    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def hotkeys(self, event):

        if event.char == "1":
            self.parent.activelabels(1)
        elif event.char == "2":
            self.parent.activelabels(2)
        elif event.char == "3":
            self.parent.activelabels(3)
        elif event.char == "4":
            self.parent.activelabels(4)
        elif event.char == "5":
            self.parent.activelabels(5)
        elif event.char == "6":
            self.parent.activelabels(6)
        elif event.char == "7":
            self.parent.activelabels(7)
        elif event.char == "8":
            self.parent.activelabels(8)
        elif event.char == "9":
            self.parent.activelabels(9)
        elif event.char == "0":
            self.parent.activelabels(10)
        elif event.char == "c":
            self.clearBBox()
        elif event.char == "a":
            self.parent.prevImage()
        elif event.char == "d":
            self.parent.nextImage()
        elif event.char == "z":
            self.parent.delBBox(True)
        elif event.char == 's':
            self.parent.saveImage()
        self.parent.activelabel.config(text='Active Label: '+str(self.parent.currentLabel+1),bg=COLORS[self.parent.currentLabel])
    def zoom(self, event):
        # self.mainPanel.move(ALL, -self.xoffset, -self.yoffset)
        if(self.scale < 3.0): #hard limit of 3x zoom to avoid excessive memory usage
            if event.num == 4 or event.delta == 120:
                self.scale *= 1.1
                self.mainPanel.scale(ALL, self.xoffset, self.yoffset, 1.1, 1.1)
        if event.num == 5 or event.delta == -120:
            self.scale *= 0.9
            self.mainPanel.scale(ALL,self.xoffset, self.yoffset, 0.9, 0.9)

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
        # self.mainPanel.move(ALL, self._x, self._y)
        self.img_id = self.mainPanel.create_image(self.xoffset, self.yoffset, image=self.tkimg, anchor=NW)
        self.mainPanel.tag_lower(self.img_id)

    def resetView(self):
        self.scale = 1.0
        self.parent.saveImage()
        self.parent.loadImage()
        self.redraw()

    def grab(self, event):
        self._y = event.y
        self._x = event.x

    def drag(self, event):

        if (self._y - event.y < 0):
            self.yoffset += 1
            self.mainPanel.move(ALL, 0, 1)
        elif (self._y - event.y > 0):
            self.yoffset -= 1
            self.mainPanel.move(ALL, 0, -1)
        if (self._x - event.x < 0):
            self.xoffset += 1
            self.mainPanel.move(ALL, 1, 0)
        elif (self._x - event.x > 0):
            self.xoffset -= 1
            self.mainPanel.move(ALL, -1, 0)

        # if self.img_id:
        #     self.mainPanel.delete(self.img_id)
        #
        # self.redraw()

        self._x = event.x
        self._y = event.y

    def loadImage(self,imagepath):
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.orig_img = self.img
        #.mainPanel.config(width=max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.parent.cur, self.parent.total))
        self.parent.clearBBox()


    def doSomething(self):
        print "You can't do that"

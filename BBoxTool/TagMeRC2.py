#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Labels objects of interest for processing
# Author:      Lucas Neves
# Company:     Neurala Inc.
# Created:     9/01/2016
# Last updated by: Lucas Neves
# Last updated: 1/26/2017
#-------------------------------------------------------------------------------
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
from TagMeMainWindow import mainwindow

BASE = RAISED
SELECTED = FLAT

# colors for the bboxes
COLORS = ['red', 'peru', 'DarkOrange1', 'green', 'green3', 'DarkSlateGray4', 'blue', 'cyan', 'orchid1', 'maroon4'] #max of 10 classes for now
# image sizes for the examples
SIZE = 256, 256

class LabelTool():
    def __init__(self, master):

        # set up the main frame
        self.parent = master
        self.parent.title("Neurala TagMeTool")
        self.frame = Frame(self.parent)
        self.parent.resizable(width=False, height=False)
        self.frame.pack(fill=BOTH, expand=False)

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

        self.classlist = []
        self.classnames= ["" for x in range(10)]
        self.classbuttons = []


        self.currentLabel = 0

        # reference to bbox
        self.bboxIdList = []

        self.bboxList = []

        self.tree = None


        self.img = None


        #popup windows
        self.top = None
        self.video_processing_window = None

        # ----------------- GUI stuff ---------------------

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 1,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 24, height = 12)
        self.listbox.grid(row = 2, column = 1, sticky = N)
        self.activelabel = Label(self.frame, text='Active Label: '+str(self.currentLabel+1),bg=COLORS[self.currentLabel])
        self.activelabel.grid(row=3,column=1,sticky=W+E+N)
        #help button
        self.help = Button(self.frame, text='Help', command= self.showhelp)
        self.help.grid(row=4, column=1, sticky=W+E+N)
        # dir entry & load
        self.ldBtn = Button(self.frame, text="Load Directory",bg='peru', command=self.loadDir)  # command
        self.ldBtn.grid(row=5, column=1, sticky=W+E+N)

        #bbox label and save
        self.labelentry = Frame(self.frame)
        self.labelentry.grid(row=6, column=1, sticky=W+E+N)
        self.labelsave = None
        self.classdefine()


        self.undo = Button(self.frame, text= 'Undo Label',state=DISABLED, command = lambda: self.delBBox(True))
        self.undo.grid(row=7, column=1, sticky=W+E+N+S)

        self.btnDel = Button(self.frame, text = 'Delete Selected',state=DISABLED, command = self.delBBox)
        self.btnDel.grid(row = 8, column = 1, sticky = W+E+S+N)
        self.btnClear = Button(self.frame, text = 'Clear All',state=DISABLED, command = self.clearBBox)
        self.btnClear.grid(row = 9, column = 1, sticky = W+E+S+N)

        # control panel for image navigation

        self.navpanel = Frame(self.frame)
        self.navpanel.grid(row = 11, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.navpanel, text='<< Prev', state=DISABLED, command = self.prevImage)
        self.prevBtn.grid(row = 1, column = 1, sticky = W+E)
        self.nextBtn = Button(self.navpanel, text='Next >>',state=DISABLED, command = self.nextImage)
        self.nextBtn.grid(row = 1, column = 2, sticky = W+E)


        # main panel for labeling
        self.mainPanel = mainwindow(self)


        self.center(self.parent)
        self.center(self.mainPanel.frame)
        self.showhelp()



    def center(self,toplevel):
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))

    def showhelp(self):
        helpview = Toplevel()
        helpview.title("TAGME TOOL INSTRUCTIONS:")
        with open('./Images/001/instructions.txt', 'r') as myfile:
            instructions = myfile.read()
        text = Message(helpview, text=instructions, bg="white")
        text.pack()
        self.center(helpview)
        helpview.lift()

    def showEnd(self):
        endview = Toplevel()
        endview.title("end of directory reached!")
        text = Message(endview, text="END OF DIRECTORY", bg="white")
        text.pack()
        self.center(endview)
        endview.lift()

    def activelabels(self,active):
        if active == 1:
            self.currentLabel = 0
        elif active == 2:
            self.currentLabel = 1
        elif active == 3:
            self.currentLabel = 2
        elif active == 4:
            self.currentLabel = 3
        elif active == 5:
            self.currentLabel = 4
        elif active == 6:
            self.currentLabel = 5
        elif active == 7:
            self.currentLabel = 6
        elif active == 8:
            self.currentLabel = 7
        elif active == 9:
            self.currentLabel = 8
        elif active == 10:
            self.currentLabel = 9
        self.activelabel.config(text='Active Label: ' + str(self.currentLabel + 1), bg=COLORS[self.currentLabel])



    def loadDir(self, dbg=False):
        #open dialog box to select data, allow only image files
        filepath = os.path.realpath(filedialog.askopenfilename(filetypes=[('data','.jpg .png .JPEG .PNG')]))

        folder_path = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        filename = os.path.splitext(filename)[0]

        self.imageDir = folder_path

        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.png'))
        if len(self.imageList) == 0:
            self.imageList = glob.glob(os.path.join(self.imageDir, '*.PNG'))
        if len(self.imageList) == 0:
            print 'No images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)
         # set up output dir
        self.outDir = os.path.join(r'%s' %(self.imageDir),'Labels')
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
            for labels in self.classlist:
                labels.config(bg='yellow')
            self.labelsave.config(bg='green', state=NORMAL)
        else:
            self.loadlabels()
            i = 0
            for buttons in self.classbuttons:
                buttons.config(bg=COLORS[i], state=NORMAL)
                i += 1

        self.loadImage()

        self.ldBtn.config(state=DISABLED, bg='gray76')

        print ' Annotations will be saved to: %s' %(self.outDir)

    def loadlabels(self):
        labelfile = os.path.join(self.outDir, "labels.txt")
        if os.path.exists(labelfile):
            with open(labelfile,"r") as labels:
                i = 0
                for label in labels:
                    self.classlist[i].insert(END, label.rstrip('\n'))
                    self.classlist[i].config(state=DISABLED)
                    i += 1
            self.bindCanvasTools()

    def readfile(self): #use  plaintext parsing
        # load labels
        self.clearBBox()
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename,'r') as f:
                reader = csv.reader(f, delimiter=" ")
                for row in reader:
                    print str(self.mainPanel.tkimg.width())
                    self.bboxList.append(row)

                    x1 = int((float(row[1])-(float(row[3])/2.0)) * self.mainPanel.tkimg.width())
                    y1 = int((float(row[2])-(float(row[4])/2.0)) * self.mainPanel.tkimg.height())
                    x2 = int((float(row[1])+(float(row[3])/2.0)) * self.mainPanel.tkimg.width())
                    y2 = int((float(row[2])+(float(row[4])/2.0)) * self.mainPanel.tkimg.height())

                    tmpId = self.mainPanel.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=COLORS[int(row[0])])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%f, %f) -> (%f, %f)' % (float(row[1]), float(row[2]), float(row[3]), float(row[4])))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[int(row[0])])
                self.mainPanel.mainPanel.scale(ALL, 0, 0, self.mainPanel.scale, self.mainPanel.scale)

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]

        self.mainPanel.loadImage(imagepath)

        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        if os.path.exists(self.labelfilename):
            self.readfile()
        self.mainPanel.redraw()

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


    def delBBox(self,last = False):
        if last:
            sel = len(self.bboxList)-1
            if sel <0:
                return
            idx=sel
        else:
            sel = self.listbox.curselection()
            if len(sel) != 1:
                return
            idx = int(sel[0])

        self.mainPanel.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.mainPanel.delete(self.bboxIdList[idx])
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
        else:
            self.showEnd()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def classdefine(self):
        for i in range(0, 10):
            lbl = Entry(self.labelentry, bg="white")
            lbl.insert(END, self.classnames[i])
            lbl.grid(row=i+1, column=2, sticky=W+E)
            self.classlist.append(lbl)
            name = Button(self.labelentry, text="Label "+(str(i+1))+":", state=DISABLED, command= lambda i=i:self.activelabels(i+1))
            name.grid(row=i+1, column=1, sticky=N+W+E)
            self.classbuttons.append(name)
        self.labelsave = Button(self.labelentry, text="Save labels", state=DISABLED, command=self.createlabels)
        self.labelsave.grid(row=12, column=2, sticky=N+S+E+W)

    def createlabels(self):
        labelfile = os.path.join(self.outDir, "labels.txt")
        i=0
        self.bindCanvasTools()

        with open(labelfile, 'w') as f:
            print len(self.classlist)
            for labels in self.classlist:
                labels.config(bg="gray76", state=DISABLED)
                print labels.get()
                f.write(str(labels.get()))
                f.write('\n')
                self.classnames[i] = str(labels.get())
                i+=1
            f.close()
        i=0
        for buttons in self.classbuttons:
            buttons.config(bg=COLORS[i], state=NORMAL)
            i+=1
        self.labelsave.config(bg='gray76',state=DISABLED)
        print "saved labels! " +labelfile

    def bindCanvasTools(self):

        self.mainPanel.bindInterface()

        self.undo.config(state=NORMAL)
        self.btnDel.config(state=NORMAL)
        self.btnClear.config(state=NORMAL)
        self.prevBtn.config(state=NORMAL)
        self.nextBtn.config(state=NORMAL)



if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()

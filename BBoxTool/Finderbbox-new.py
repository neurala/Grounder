#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bounding boxes for Ground Truthing data
# Author:      Lucas Neves
# Company:     Neurala Inc.
# Created:     9/01/2016
# Last updated by: Lucas Neves
# Last updated: 10/10/2016
#-------------------------------------------------------------------------------
from __future__ import division

from Tkinter import *
import tkFileDialog as filedialog
from PIL import Image, ImageTk
import os
import glob
import csv
import subprocess

BASE = RAISED
SELECTED = FLAT

# colors for the bboxes
COLORS = ['red', 'yellow', 'DarkOrange1', 'green', 'green3', 'DarkSlateGray4', 'blue', 'cyan', 'orchid1','maroon4'] #max of 7 classes for now
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
        self.classnames= ["" for x in range(10)]
        self.classbuttons = []
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


        self.xoffset=0.0
        self.yoffset=0.0
        self.scaleimg = None
        self.currentImage = None
        self.currentLabel = 0


        self.scale = 1.0
        self.orig_img = None
        self.img = None
        self.img_id = None
        # ----------------- GUI stuff ---------------------

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, bd=0, cursor='tcross')


        self.mainPanel.grid(row=1, column=1, rowspan=13, sticky=N+W)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 24, height = 12)
        self.listbox.grid(row = 2, column = 2, sticky = N)
        self.activelabel = Label(self.frame, text='Active Label: '+str(self.currentLabel+1),bg=COLORS[self.currentLabel])
        self.activelabel.grid(row=3,column=2,sticky=W+E+N)
        #help button
        self.help = Button(self.frame, text='Help', command= self.showhelp)
        self.help.grid(row=4, column=2, sticky=W+E+N)
        # dir entry & load
        self.ldBtn = Button(self.frame, text="Load Directory",bg='yellow', command=self.loadDir)  # command
        self.ldBtn.grid(row=5, column=2, sticky=W+E+N)

        #bbox label and save
        self.labelentry = Frame(self.frame)
        self.labelentry.grid(row=6, column=2, sticky=W+E+N)
        self.labelsave = None
        self.classdefine()


        self.undo = Button(self.frame, text= 'Undo Label',state=DISABLED, command = lambda: self.delBBox(True))
        self.undo.grid(row=7, column=2, sticky=W+E+N+S)

        self.btnDel = Button(self.frame, text = 'Delete Selected',state=DISABLED, command = self.delBBox)
        self.btnDel.grid(row = 8, column = 2, sticky = W+E+S+N)
        self.btnClear = Button(self.frame, text = 'Clear All',state=DISABLED, command = self.clearBBox)
        self.btnClear.grid(row = 9, column = 2, sticky = W+E+S+N)




        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 10, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', state=DISABLED, width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>',state=DISABLED, width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', state=DISABLED, command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        self.mainPanel.focus_set()
        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        self.parent.bind("<Left>", self.prevImage)
        self.parent.bind("<Right>", self.nextImage)
        self.top = None
        self.video_processing_window = None
        self.splash()



        #self.showhelp()
        self.init = True

    def splash(self):
        raw_img = Image.open("./Images/001/test.jpeg") #SPLASH SCREEN SOURCE GOES HERE
        self.tkimg = ImageTk.PhotoImage(raw_img)
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)

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
        helpview.title("Finder Ground Truthing Utility:")
        instructions = "\t\t How to Use this Utility \n" \
                       "1. Click on load directory\n\n" \
                       "2. Navigate to the desired dataset directory and select any image within\n\n" \
                       "3. Once directory is loaded, the first image will appear\n\n" \
                       "4. Enter the desired names for each label and click 'update label'. NOTE: You do not need to use all labels\n\n" \
                       "5. Use the number keys, or click the labels and draw bounding boxes on the image by clicking and dragging to create the desired bounding box\n\n" \
                       "6. Once done with a given frame, use the 'Next' or hotkeys to automatically save and move on to the next image in the set\n\n" \
                       "HOTKEYS:\n" \
                       "'a' or left = prev frame\n" \
                       "'d' or right = next frame\n" \
                       "'z' = undo\n" \
                       "'c' = clear\n" \
                       "1-7 = switch labels\n" \
                       "'s' = manual save\n"
        text = Message(helpview, text=instructions, bg="white")
        text.pack()
        self.center(helpview)

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

    def hotkeys(self, event):

        if event.char == "1":
            self.activelabels(1)
        elif event.char == "2":
            self.activelabels(2)
        elif event.char == "3":
            self.activelabels(3)
        elif event.char == "4":
            self.activelabels(4)
        elif event.char == "5":
            self.activelabels(5)
        elif event.char == "6":
            self.activelabels(6)
        elif event.char == "7":
            self.activelabels(7)
        elif event.char == "8":
            self.activelabels(8)
        elif event.char == "9":
            self.activelabels(9)
        elif event.char == "0":
            self.activelabels(10)
        elif event.char == "c":
            self.clearBBox()
        elif event.char == "a":
            self.prevImage()
        elif event.char == "d":
            self.nextImage()
        elif event.char == "z":
            self.delBBox(True)
        elif event.char == 's':
            self.saveImage()
        self.activelabel.config(text='Active Label: '+str(self.currentLabel+1),bg=COLORS[self.currentLabel])

    def loadDir(self, dbg=False):

        filepath = os.path.realpath(filedialog.askopenfilename(filetypes=[('data','.jpg .mp4 .avi .mov')]))

        folder_path = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        filename = os.path.splitext(filename)[0]

        if os.path.splitext(filepath)[1] in {'.mp4','.avi','.mov'}:
            self.imageDir = os.path.join(r'%s' % (folder_path), filename)
            if not os.path.exists(self.imageDir):
                os.mkdir(self.imageDir)
                self.videoProcessing(filepath, filename)
        else:
            self.imageDir = folder_path

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
                i =0
                for label in labels:
                    self.classlist[i].insert(END, label.rstrip('\n'))
                    self.classlist[i].config(state=DISABLED)
                    i+=1
            self.bindCanvasTools()

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
                    x1 = int((float(row[1])-(float(row[3])/2.0)) * self.tkimg.width())
                    y1 = int((float(row[2])-(float(row[4])/2.0)) * self.tkimg.height())
                    x2 = int((float(row[1])+(float(row[3])/2.0)) * self.tkimg.width())
                    y2 = int((float(row[2])+(float(row[4])/2.0)) * self.tkimg.height())
                    tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=COLORS[int(row[0])])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '(%f, %f) -> (%f, %f)' % (float(row[1]), float(row[2]), float(row[3]), float(row[4])))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                            fg=COLORS[int(row[0])])
                self.mainPanel.scale(ALL, 0, 0, self.scale, self.scale)

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
        self.redraw()

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
        if event.num == 4 or event.delta == 120:
            self.scale *= 1.1
            self.mainPanel.scale(ALL, 0, 0, 1.1, 1.1)
        if event.num == 5 or event.delta == -120:
            self.scale *= 0.9
            self.mainPanel.scale(ALL, 0, 0, 0.9, 0.9)

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

    def mouseRelease(self,event):
        x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
        y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)

        self.mainPanel.itemconfig(self.bboxId, dash=(2,2))
        self.bboxIdList.append(self.bboxId)
        width= x2-x1
        height= y2-y1
        self.bboxList.append((self.currentLabel, float((x1+(width/2.0)) / self.tkimg.width()), float((y1+(height/2.0)) / self.tkimg.height()),
                              float(width / self.tkimg.width()), float(height / self.tkimg.height())))

        self.bboxId = None
        self.listbox.insert(END, '(%d, %d) -> (%d, %d)' % (x1, y1, x2, y2))
        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[self.currentLabel])
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
                                                            outline = COLORS[self.currentLabel],dash=(2, 4))

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

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

        lbl1 = Entry(self.labelentry,bg="white")
        lbl1.insert(END, self.classnames[0])
        lbl1.grid(row=1, column=2, sticky=W + E)
        self.classlist.append(lbl1)
        name1 = Button(self.labelentry,text="Label 1:",state=DISABLED, command= lambda:self.activelabels(1))
        name1.grid(row=1, column=1, sticky=N + W + E)
        self.classbuttons.append(name1)
        lbl2 = Entry(self.labelentry,bg="white")
        lbl2.insert(END, self.classnames[1])
        lbl2.grid(row=2, column=2, sticky=W + E)
        self.classlist.append(lbl2)
        name2 = Button(self.labelentry,text="Label 2:",state=DISABLED,command= lambda:self.activelabels(2))
        name2.grid(row=2, column=1, sticky=N + W + E)
        self.classbuttons.append(name2)
        lbl3 = Entry(self.labelentry,bg="white")
        lbl3.insert(END, self.classnames[2])
        lbl3.grid(row=3, column=2, sticky=W + E)
        self.classlist.append(lbl3)
        name3 = Button(self.labelentry, text="Label 3:",state=DISABLED, command= lambda:self.activelabels(3))
        name3.grid(row=3, column=1, sticky=N + W + E)
        self.classbuttons.append(name3)
        lbl4 = Entry(self.labelentry, bg="white")
        lbl4.insert(END, self.classnames[3])
        lbl4.grid(row=4, column=2, sticky=W + E)
        self.classlist.append(lbl4)
        name4 = Button(self.labelentry, text="Label 4:",state=DISABLED, command= lambda:self.activelabels(4))
        name4.grid(row=4, column=1, sticky=N + W + E)
        self.classbuttons.append(name4)
        lbl5 = Entry(self.labelentry, bg="white")
        lbl5.insert(END, self.classnames[4])
        lbl5.grid(row=5, column=2, sticky=W + E)
        self.classlist.append(lbl5)
        name5 = Button(self.labelentry, text="Label 5:",state=DISABLED, command= lambda:self.activelabels(5))
        name5.grid(row=5, column=1, sticky=N + W + E)
        self.classbuttons.append(name5)
        lbl6 = Entry(self.labelentry, bg="white")
        lbl6.insert(END, self.classnames[5])
        lbl6.grid(row=6, column=2, sticky=W + E)
        self.classlist.append(lbl6)
        name6 = Button(self.labelentry,text="Label 6:",state=DISABLED, command= lambda:self.activelabels(6))
        name6.grid(row=6, column=1, sticky=N + W + E)
        self.classbuttons.append(name6)
        lbl7 = Entry(self.labelentry,bg="white")
        lbl1.insert(END, self.classnames[6])
        lbl7.grid(row=7, column=2, sticky=W + E)
        self.classlist.append(lbl7)
        name7 = Button(self.labelentry, text="Label 7:",state=DISABLED, fg="white", command= lambda: self.activelabels(7))
        name7.grid(row=7, column=1, sticky=N + W + E)
        self.classbuttons.append(name7)
        lbl8 = Entry(self.labelentry,bg="white")
        lbl8.grid(row=8, column=2, sticky=W + E)
        self.classlist.append(lbl8)
        name8 = Button(self.labelentry, text="Label 8:",state=DISABLED, command= lambda: self.activelabels(8))
        name8.grid(row=8, column=1, sticky=N + W + E)
        self.classbuttons.append(name8)
        lbl9 = Entry(self.labelentry, bg="white")
        lbl9.grid(row=9, column=2, sticky=W + E)
        self.classlist.append(lbl9)
        name9 = Button(self.labelentry, text="Label 9:",state=DISABLED, command= lambda: self.activelabels(9))
        name9.grid(row=9, column=1, sticky=N + W + E)
        self.classbuttons.append(name9)
        lbl10 = Entry(self.labelentry,bg="white")
        lbl10.grid(row=10, column=2, sticky=W + E)
        self.classlist.append(lbl10)
        name10 = Button(self.labelentry, text="Label 10:",state=DISABLED, command= lambda: self.activelabels(10))
        name10.grid(row=10, column=1, sticky=N + W + E)
        self.classbuttons.append(name10)
        self.labelsave = Button(self.labelentry, text="Save labels", state=DISABLED, command=self.createlabels)
        self.labelsave.grid(row=12,column=2, sticky=N+S+E+W)

    def createlabels(self):
        labelfile = os.path.join(self.outDir, "labels.txt")
        i=0
        self.labelsave.config(bg='gray76',state=DISABLED)
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
            buttons.config(bg=COLORS[i],state=NORMAL)
            i+=1
        print "saved labels! " +labelfile

    def videoProcessing(self, videopath,filename):

        self.video_processing_window = Toplevel()

        duration = subprocess.check_output(['ffprobe', '-i', videopath, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
        fps_check = subprocess.check_output(['ffprobe', '-i', videopath, '-show_entries', 'stream=avg_frame_rate', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])

        fps = eval(fps_check)

        title = Label(self.video_processing_window, text='Video Information')
        title.grid(row=1, column=1, sticky=W + N)
        title = Label(self.video_processing_window, text='Sampling Parameters')
        title.grid(row=1, column=2, sticky=W + N)

        frames_per_second = Label(self.video_processing_window, text='FPS: '+str(fps))
        frames_per_second.grid(row=2, column=1, sticky=W + N)

        video_length = Label(self.video_processing_window, text='Length(seconds): '+duration)
        video_length.grid(row=3, column=1, sticky=W + N)

        set_video_start_label = Label(self.video_processing_window, text='Start time(seconds): ')
        set_video_start_label.grid(row=3, column=2, sticky=W + N)

        set_video_end_label = Label(self.video_processing_window, text='End time(seconds): ')
        set_video_end_label.grid(row=4, column=2, sticky=W + N)

        set_target_fps_label = Label(self.video_processing_window, text='sample rate(FPS): ')
        set_target_fps_label.grid(row=2, column=2, sticky=W + N)

        set_target_fps = Entry(self.video_processing_window, bg="white")
        set_target_fps.grid(row=2, column=3, sticky=W + E)

        set_video_start = Entry(self.video_processing_window, bg="white")
        set_video_start.grid(row=3, column=3, sticky=W + E)

        set_video_end = Entry(self.video_processing_window, bg="white")
        set_video_end.grid(row=4, column=3, sticky=W + E)



        do_slices_button = Button(self.video_processing_window, text="Sample Video", command=lambda: self.doSlices(float(fps), float(duration), set_target_fps.get(), set_video_start.get(), set_video_end.get(),filename,videopath))
        do_slices_button.grid(row=5, column=2, sticky=W+E)
        self.video_processing_window.grab_set()
        self.parent.wait_window(self.video_processing_window)

    def doSlices(self, native_fps, native_duration, fps, start, end,filename,videopath):

        if float(start) < float(end):
            print "good video range"
            print native_fps
            print fps
            if float(fps) <= float(native_fps):
                print "good framerate"
                if float(end) <= float(native_duration):
                    print "slicing video"
                    segment = float(end) - float(start)
                    slices = subprocess.check_output(['ffmpeg', '-i', videopath,'-ss',str(start),'-t',str(segment), '-q:v', '2', '-r', str(fps), self.imageDir+"/"+filename+"%5d.jpg"])
                    self.video_processing_window.destroy()

    def bindCanvasTools(self):
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<ButtonRelease-1>", self.mouseRelease)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Escape> to cancel current bbox self.cancelBBox
        self.mainPanel.bind("<Key>", self.hotkeys)
        self.mainPanel.config(scrollregion=self.mainPanel.bbox(ALL))

        self.mainPanel.bind("<Button-4>", self.zoom)
        self.mainPanel.bind("<Button-5>", self.zoom)

        self.mainPanel.bind("<MouseWheel>", self.zoom)
        self.undo.config(state=NORMAL)
        self.btnDel.config(state=NORMAL)
        self.btnClear.config(state=NORMAL)
        self.prevBtn.config(state=NORMAL)
        self.nextBtn.config(state=NORMAL)
        self.goBtn.config(state=NORMAL)
        self.idxEntry.config(bg='white')

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()

from __future__ import division
import os
import shutil
import webbrowser
from Tkinter import *
from threading import Thread
import subprocess
class filePackage():

    def __init__(self, directory):
        self.origindir = directory
        self.targetOutput = os.path.abspath(os.path.join(self.origindir, ".."))
        self.text = None
        self.button = None
        self.upload_button = None
        self.compressview = None
        self.thread = None
        self.confirm()

    def confirm(self):
        self.confirmView = Toplevel()
        self.confirmView.title("COMPRESSING")
        warning = Message(self.confirmView,text="THIS OPERATION IS TIME CONSUMING \nThis operation could take a very long time, are you sure you want to continue?", bg="white" , aspect=500)
        warning.pack()
        self.confirmbtn = Button(self.confirmView, text="Yes I can wait",command=self.doCompression)
        self.confirmbtn.pack(fill="x")
        self.cancelbtn = Button(self.confirmView, text="No I'll do it later",command=self.confirmView.destroy)
        self.cancelbtn.pack(fill="x")
        self.center(warning)

    def doCompression(self):
        self.confirmView.destroy()
        self.compressview = Toplevel()
        self.compressview.protocol('WM_DELETE_WINDOW',self.close)
        if(os.name =='nt'):
            iconpath = os.path.realpath("./Images/001/logo.ico")
            self.compressview.iconbitmap(iconpath)

        self.compressview.title("COMPRESSING")
        self.text = Message(self.compressview, text="Compressing, please wait. This could take a while.", bg="white" , aspect=500)
        self.text.pack()
        self.thread = Thread(target=self.comp)
        self.thread.start()

    def comp(self):
         shutil.make_archive(os.path.join(self.targetOutput,os.path.dirname(self.origindir)+"_package"), 'zip', self.origindir)
         self.text.config(text="compression complete! file saved to: \n"+self.targetOutput)
         self.text.pack()
         self.upload_button = Button(self.compressview, text='Upload', command = self.upload)
         button = Button(self.compressview, text= 'Close', command = self.compressview.destroy)
         button.pack(fill="x")
         self.upload_button.pack(fill="x")
         self.center(self.compressview)

    def close(self):
        #do nothing
        print "use Exit button"

    def upload(self):
        webbrowser.open_new("http://www.brainsforbots.com")

    def center(self,toplevel):
        toplevel.update_idletasks()
        #get screen resolution
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        #get window size
        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        #compute center
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))

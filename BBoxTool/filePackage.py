import os
import shutil
import webbrowser
from Tkinter import *
class filePackage():
    def __init__(self, directory):
        self.origindir = directory
        self.targetOutput = os.path.abspath(os.path.join(self.origindir, ".."))
        self.doCompression()

    def doCompression(self):
        compressview = Toplevel()
        if(os.name =='nt'):
            iconpath = os.path.realpath("./Images/001/logo.ico")
            compressview.iconbitmap(iconpath)
        self.center(compressview)
        compressview.title("COMPRESSING")
        text = Message(compressview, text="Compressing, please wait. this could take a while", bg="white")
        text.pack()
        button = Button(compressview, text= 'exit', command = compressview.destroy)
        button.pack()
        shutil.make_archive(os.path.join(self.targetOutput,os.path.dirname(self.origindir)+"package"), 'gztar', self.origindir)
        text.config(text="compression complete! file saved to"+self.targetOutput)
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


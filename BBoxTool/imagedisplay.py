from Tkinter import *
from PIL import Image, ImageTk


class GUI:
    def __init__(self,root):
        frame = Frame(root, bd=2, relief=SUNKEN)

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        xscrollbar = Scrollbar(frame, orient=HORIZONTAL)
        xscrollbar.grid(row=1, column=0, sticky=E+W)
        yscrollbar = Scrollbar(frame)
        yscrollbar.grid(row=0, column=1, sticky=N+S)
        self.canvas = Canvas(frame, bd=0, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set, xscrollincrement = 10, yscrollincrement = 10)
        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)

        File = "./5.ppm"

        self.img = ImageTk.PhotoImage(Image.open(File))
        self.canvas.create_image(0,0,image=self.img, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox(ALL))
        self.scale = 1.0
        self.orig_img = Image.open(File)
        self.img = None
        self.img_id = None
        # draw the initial image at 1x scale

        xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)

        frame.pack()

        self.canvas.bind("<Button 3>",self.grab)
        self.canvas.bind("<B3-Motion>",self.drag)
        self.canvas.bind("<Button-4>", self.zoom)
        self.canvas.bind("<Button-5>", self.zoom)
        self.redraw()

    def grab(self,event):
        self._y = event.y
        self._x = event.x

    def drag(self,event):
        if (self._y-event.y < 0): self.canvas.yview("scroll",-1,"units")
        elif (self._y-event.y > 0): self.canvas.yview("scroll",1,"units")
        if (self._x-event.x < 0): self.canvas.xview("scroll",-1,"units")
        elif (self._x-event.x > 0): self.canvas.xview("scroll",1,"units")
        self._x = event.x
        self._y = event.y

    def zoom(self,event):
        if event.num == 4:
            self.scale *= 2
        elif event.num == 5:
            self.scale *= 0.5
        self.redraw(event.x, event.y)

    def redraw(self, x=0, y=0):
        if self.img_id:
            self.canvas.delete(self.img_id)
        iw, ih = self.orig_img.size
        size = int(iw * self.scale), int(ih * self.scale)
        self.img = ImageTk.PhotoImage(self.orig_img.resize(size))
        self.img_id = self.canvas.create_image(x, y, image=self.img)

        # tell the canvas to scale up/down the vector objects as well
        self.canvas.scale(ALL, x, y, self.scale, self.scale)

root = Tk()
GUI(root)
root.mainloop()
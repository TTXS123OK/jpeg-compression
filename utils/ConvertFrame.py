from typing import Union
from tkinter import *
from PIL import Image, ImageTk


class ConvertFrame:
    def __init__(self, parent_frame: Union[Frame, Tk]):
        self.parent_frame = parent_frame
        self.frame = Frame(self.parent_frame)

        self.bmp_path = StringVar()
        self.bmp_img = ""
        self.bmp_frame = Label(
            self.frame,
            image=self.bmp_img,
            # textvariable=self.bmp_path,
            # compound='top'
        )

        self.arrow_path = 'assets/arrow.png'
        self.arrow_img = ImageTk.PhotoImage(Image.open(self.arrow_path))
        self.arrow_frame = Label(
            self.frame,
            image=self.arrow_img
        )

        self.jpeg_path = 'assets/tmp.jpeg'
        self.jpeg_img = None
        self.jpeg_frame = Label(
            self.frame,
        )

    def set_bmp(self, bmp_path: str):
        self.bmp_path.set(bmp_path)
        self.bmp_img = ImageTk.PhotoImage(Image.open(self.bmp_path.get()))
        self.bmp_frame['image'] = self.bmp_img

    def reset_bmp(self):
        self.bmp_path.set("")
        self.bmp_img = ""
        self.bmp_frame['image'] = self.bmp_img

    def grid(self, row: int, column: int, columnspan: int):
        self.frame.grid(row=row, column=column, columnspan=columnspan)

    def update(self, state: str):
        for widget in self.frame.winfo_children():
            widget.grid_remove()
        if state == 'UNLOADED':
            ''' do nothing '''
        elif state == 'LOADED':
            self.bmp_frame.grid(row=1, column=1)
        else:  # state == 'COMPRESSED'
            self.jpeg_img = ImageTk.PhotoImage(Image.open(self.jpeg_path))
            self.jpeg_frame['image'] = self.jpeg_img
            self.bmp_frame.grid(row=1, column=1)
            self.arrow_frame.grid(row=1, column=2)
            self.jpeg_frame.grid(row=1, column=3)
        Frame(self.frame).grid()

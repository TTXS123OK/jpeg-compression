import os
from utils.ImgFrame import ImgFrame

from tkinter import Frame


class ConvertFrame:
    def __init__(self, parent_frame):
        self.__frame = Frame(parent_frame)
        self.__parent_frame = parent_frame
        self.bmp_frame = ImgFrame(self.__frame, img_type='bmp', show_image_path=True)
        self.arrow = ImgFrame(self.__frame, img_path=os.path.join(os.getcwd(), 'assets/arrow.png'))
        self.jpeg_frame = ImgFrame(self.__frame, img_path=os.path.join(os.getcwd(), 'tmp/tmp.jpeg'))

    def grid(self, row: int, column: int, columnspan: int, state: str):
        if state == 'UNLOADED':
            pass
        elif state == 'LOADED' or state == 'COMPRESSING':
            self.bmp_frame.grid(row=1, column=1)
        else:
            self.bmp_frame.grid(row=1, column=1)
            self.arrow.grid(row=1, column=2)
            self.jpeg_frame.grid(row=1, column=3)
        self.__frame.grid(row=row, column=column, columnspan=columnspan)

    def update(self, state: str):
        if state == 'UNLOADED':
            self.bmp_frame.reset_img()
            self.bmp_frame.reset_frame()
            self.arrow.reset_frame()
            self.jpeg_frame.reset_frame()
        elif state == 'LOADED':
            self.arrow.reset_frame()
            self.jpeg_frame.reset_frame()
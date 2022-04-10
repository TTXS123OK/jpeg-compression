from tkinter import *
from PIL import Image, ImageTk


class ImgFrame:
    def __init__(self, parent_frame, img_type='all', img_path=None, show_image_path=False):
        self.__parent_frame = parent_frame
        self.__row = None
        self.__column = None
        self.__columnspan = None

        self.img_type = img_type
        self.__show_image_path = show_image_path
        self.__img_path = None
        self.__image = None
        self.__tk_image = None

        self.__frame = None
        self.__label = None

        self.__init_frame()
        self.set_img(img_path)

    def __init_frame(self):
        self.__frame = Frame(self.__parent_frame)
        # self.__frame.rowconfigure(1, weight=1)
        # self.__frame.columnconfigure(1, weight=1)
        self.__frame.grid(column=self.__column, row=self.__row, columnspan=self.__columnspan)

    def grid(self, row=1, column=1, columnspan=1):
        self.__row = row
        self.__column = column
        self.__columnspan = columnspan
        self.show()

    def show(self):
        if self.__img_path is not None:
            self.reset_frame()
            self.__image = Image.open(self.__img_path)
            self.__tk_image = ImageTk.PhotoImage(self.__image)
            self.__label = Label(self.__frame, text=self.__img_path, image=self.__tk_image)
            if self.__show_image_path:
                self.__label['compound'] = 'top'
            # print(self.__label.configure())
            self.__label.grid()

    def reset_frame(self):
        # for widget in self.__frame.winfo_children(): # clear last bmp image
        #         widget.destroy()
        self.__frame.destroy()
        self.__init_frame()

    def set_img(self, img_path):
        self.__img_path = img_path

    def reset_img(self):
        self.__img_path = None
        self.__image = None
        self.__tk_image = None

    def get_img(self):
        return self.__img_path


# usage demo

if __name__ == "__main__":
    
    path1 = '../warma.bmp'

    root = Tk()  # init tk window

    f = ImgFrame(root, img_path=path1)  # set bmp frame

    # f.label.bind('<ButtonPress-1>', lambda e: f.set_bmp(path2)) # click to change bmp image

    root.mainloop()  # show tk window

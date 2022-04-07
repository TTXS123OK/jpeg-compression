from tkinter import *
from tkinter.filedialog import askopenfile
from ImgFrame import ImgFrame


class View:

    def __init__(self):
        self.main_frame = Tk()
        self.main_frame.title("BMP to JPEG Converter")

        self.bmp_frame = ImgFrame(self.main_frame, column=1, row=2)
        self.load_btn = Button(self.main_frame, text="Select BMP File", command=lambda: open_file(self.bmp_frame))
        self.clear_btn = Button(self.main_frame, text="Clear BMP File", command=lambda: bmp_frame.clear())
        self.compress_btn = Button(self.main_frame, text="Compress", command=lambda: bmp_frame.clear())
        self.save_btn = Button(self.main_frame, text="Save JPEG File", command=lambda: bmp_frame.clear())
        self.cancel_compress_btn = Button(self.main_frame, text="Cancel Compress", command=lambda: bmp_frame.clear())
        self.Compress_ratio_text = Label(self.main_frame, text="Compress Ratio: Unknown")

    def show(self):
        self.bmp_frame.show()
        self.load_btn.grid(column=1, row=1)
        self.clear_btn.grid(column=1, row=3)
        self.compress_btn.grid(column=2, row=1)
        self.save_btn.grid(column=3, row=1)
        self.cancel_compress_btn.grid(column=3, row=3)
        self.Compress_ratio_text.grid(column=2, row=3)
        self.main_frame.mainloop()


def open_file(img_frame: ImgFrame):
    file = askopenfile(mode='r', filetypes=[('image', '*.bmp'), ('image', '*.jpg')])
    if file is not None:
        img_frame.set_img(file.name)
        img_frame.show()


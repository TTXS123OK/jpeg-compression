import os.path
from enum import Enum

from tkinter import *
from PIL import Image
import numpy as np

from tkinter.filedialog import askopenfile, asksaveasfilename
from utils.ConvertFrame import ConvertFrame
from utils.JPEGModel import JPEG


class View:
    pass


class Model:
    class State(Enum):
        UNLOADED = 0
        LOADED = 1
        COMPRESSED = 2

    def __init__(self):
        self.view = None

        self.state = Model.State.UNLOADED
        self.bmp_path = None
        self.img = None
        self.tmp_file_path = "assets/tmp.jpeg"
        self.compress_ratio = 'UNKNOWN'

    def set_view(self, view: View) -> None:
        assert view is not None, "Model set view failed"
        self.view = view

    def update_view(self) -> None:
        self.view.update()

    def set_state(self, state: State) -> None:
        self.state = state

    def get_state(self) -> State:
        return self.state

    def clear_bmp(self) -> None:
        self.state = Model.State.UNLOADED
        self.bmp_path = None
        self.img = None
        self.compress_ratio = 'UNKNOWN'
        self.update_view()

    def set_bmp_path(self, file_path: str) -> None:
        self.bmp_path = file_path
        self.img = Image.open(file_path)
        self.set_state(Model.State.LOADED)
        self.update_view()

    def compress(self) -> None:
        self.view.jpeg = JPEG()
        height, width = self.img.size
        rgb = list(np.array(self.img.getdata()).reshape((height, width, 3)))
        self.view.jpeg.compress_from_rgb(rgb)
        with open(self.tmp_file_path, "wb") as f:
            self.view.jpeg.write(f)
        self.set_state(Model.State.COMPRESSED)
        self.compress_ratio = "%.6f" % (os.path.getsize(self.bmp_path) / os.path.getsize(self.tmp_file_path))
        self.update_view()

    def cancel_compress(self) -> None:
        self.set_state(Model.State.LOADED)
        self.compress_ratio = 'UNKNOWN'
        self.update_view()


class Control:

    def __init__(self):
        self.model = None

    def set_model(self, model: Model) -> None:
        assert model is not None, "Control set_model failed"
        self.model = model

    def open_file(self, img_type) -> None:
        file = None
        if img_type == 'all':
            file = askopenfile(mode='r', filetypes=[('image', '*')])
        elif img_type == 'bmp':
            file = askopenfile(mode='r', filetypes=[('image', '*.bmp')])
        if file is not None:
            self.model.set_bmp_path(file.name)

    def save_file(self) -> None:
        new_path = asksaveasfilename(filetypes=[('image', '*.jpeg')])
        if new_path is not None:
            os.popen('cp %s %s' % (self.model.tmp_file_path, new_path))

    def clear_all(self) -> None:
        self.model.clear_bmp()

    def compress(self) -> None:
        self.model.compress()

    def cancel_compress(self) -> None:
        self.model.cancel_compress()


class View:

    def __init__(self, model: Model = None, control: Control = None):
        self.model = model
        self.control = control

        self.jpeg = None

        self.main_frame = Tk()
        self.main_frame.title("BMP to JPEG Converter")
        self.compress_ratio_text = StringVar(value='Compress Ratio: UNKNOWN')

        self.convert_frame = ConvertFrame(self.main_frame)
        self.load_btn = Button(self.main_frame, text="Select BMP File", command=lambda: self.control.open_file('bmp'))
        self.clear_btn = Button(self.main_frame, text="Clear BMP File", command=lambda: self.control.clear_all())
        self.compress_btn = Button(self.main_frame, text="Compress", command=lambda: self.control.compress())
        self.save_btn = Button(self.main_frame, text="Save JPEG File", command=lambda: self.control.save_file())
        self.cancel_compress_btn = Button(self.main_frame, text="Cancel Compress",
                                          command=lambda: self.control.cancel_compress())
        self.Compress_ratio_text = Label(self.main_frame, textvariable=self.compress_ratio_text)

    def set_model(self, model: Model) -> None:
        assert model is not None, "View set model failed"
        self.model = model

    def set_control(self, control: Control) -> None:
        assert control is not None, "View set control failed"
        self.control = control

    def update(self) -> None:
        self.compress_ratio_text.set('Compress Ratio: ' + self.model.compress_ratio)

        if self.model.get_state() == Model.State.UNLOADED:
            self.load_btn['state'] = 'normal'
            self.clear_btn['state'] = 'disabled'
            self.compress_btn['state'] = 'disabled'
            self.save_btn['state'] = 'disabled'
            self.cancel_compress_btn['state'] = 'disabled'
            self.convert_frame.update('UNLOADED')
        elif self.model.get_state() == Model.State.LOADED:
            self.convert_frame.set_bmp(self.model.bmp_path)
            self.load_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'normal'
            self.compress_btn['state'] = 'normal'
            self.save_btn['state'] = 'disabled'
            self.cancel_compress_btn['state'] = 'disabled'
            self.convert_frame.update('LOADED')
        else:  # self.model.get_state() == Model.State.COMPRESSED
            self.load_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'normal'
            self.compress_btn['state'] = 'disabled'
            self.save_btn['state'] = 'normal'
            self.cancel_compress_btn['state'] = 'normal'
            self.convert_frame.update('COMPRESSED')

    def show(self) -> None:
        self.convert_frame.grid(row=2, column=1, columnspan=3)
        self.load_btn.grid(row=1, column=1)
        self.clear_btn.grid(row=3, column=1)
        self.compress_btn.grid(row=1, column=2)
        self.save_btn.grid(row=1, column=3)
        self.cancel_compress_btn.grid(row=3, column=3)
        self.Compress_ratio_text.grid(row=3, column=2)
        self.main_frame.mainloop()

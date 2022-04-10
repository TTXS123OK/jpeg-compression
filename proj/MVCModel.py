import os.path
import time
from enum import Enum
import PIL

from tkinter import *
from tkinter.filedialog import askopenfile

from utils.ConvertFrame import ConvertFrame


class View:
    pass


class Model:
    class State(Enum):
        UNLOADED = 0
        LOADED = 1
        COMPRESSING = 2
        COMPRESSED = 3

    def __init__(self):
        self.view = None

        self.state = Model.State.UNLOADED
        self.img_path = None
        self.img = None
        self.__compress_ratio = 'UNKNOWN'

    def set_view(self, view: View):
        assert view is not None, "Model set view failed"
        self.view = view

    def set_state(self, state: State):
        self.state = state

    def get_state(self) -> State:
        return self.state

    def update_view(self):
        self.view.update()

    def reset_img(self):
        self.state = Model.State.UNLOADED
        self.__compress_ratio = 'UNKNOWN'
        self.img_path = None
        self.img = None
        self.update_view()

    def set_img(self, file_path):
        self.img_path = file_path
        self.img = PIL.Image.open(file_path)
        self.set_state(Model.State.LOADED)
        self.update_view()

    def compress(self):
        tmp_path = os.path.join(os.getcwd(), 'tmp/tmp.jpeg')
        self.set_state(Model.State.COMPRESSING)
        # self.update_view()
        time.sleep(1)
        self.img.save(tmp_path)
        self.set_state(Model.State.COMPRESSED)
        self.__compress_ratio = str(os.path.getsize(self.img_path) / os.path.getsize(tmp_path))
        self.update_view()

    def cancel_compress(self):
        self.set_state(Model.State.LOADED)
        self.__compress_ratio = 'UNKNOWN'
        self.update_view()

    def get_comress_ratio(self):
        return self.__compress_ratio


class Control:

    def __init__(self):
        self.model = None

    def set_model(self, model: Model):
        assert model is not None, "Control set_model failed"
        self.model = model

    def open_file(self, img_type):
        file = None
        if img_type == 'all':
            file = askopenfile(mode='r', filetypes=[('image', '*')])
        elif img_type == 'bmp':
            file = askopenfile(mode='r', filetypes=[('image', '*.bmp')])
        if file is not None:
            self.model.set_img(file.name)

    def clear_all(self):
        self.model.reset_img()

    def compress(self):
        self.model.compress()

    def cancel_compress(self):
        self.model.cancel_compress()


class View:

    def __init__(self, model: Model = None, control: Control = None):
        self.model = model
        self.control = control

        self.main_frame = Tk()
        self.main_frame.title("BMP to JPEG Converter")
        self.__compress_ratio = StringVar(value='Compress Ratio: UNKNOWN')

        self.convert_frame = ConvertFrame(self.main_frame)
        self.load_btn = Button(self.main_frame, text="Select BMP File", command=lambda: self.control.open_file('bmp'))
        self.clear_btn = Button(self.main_frame, text="Clear BMP File", command=lambda: self.control.clear_all())
        self.compress_btn = Button(self.main_frame, text="Compress", command=lambda: self.control.compress())
        self.save_btn = Button(self.main_frame, text="Save JPEG File")
        self.cancel_compress_btn = Button(self.main_frame, text="Cancel Compress",
                                          command=lambda: self.control.cancel_compress())
        self.Compress_ratio_text = Label(self.main_frame, textvariable=self.__compress_ratio)

    def set_model(self, model: Model):
        assert model is not None, "View set model failed"
        self.model = model

    def set_control(self, control: Control):
        assert control is not None, "View set control failed"
        self.control = control

    def update(self):
        self.__compress_ratio.set('Compress Ratio: ' + self.model.get_comress_ratio())
        if self.model.get_state() == Model.State.UNLOADED:
            self.convert_frame.update('UNLOADED')
            self.load_btn['state'] = 'normal'
            self.clear_btn['state'] = 'disabled'
            self.compress_btn['state'] = 'disabled'
            self.save_btn['state'] = 'disabled'
            self.cancel_compress_btn['state'] = 'disabled'
        elif self.model.get_state() == Model.State.LOADED:
            self.convert_frame.bmp_frame.set_img(self.model.img_path)
            self.convert_frame.update('LOADED')
            self.load_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'normal'
            self.compress_btn['state'] = 'normal'
            self.save_btn['state'] = 'disabled'
            self.cancel_compress_btn['state'] = 'disabled'
        elif self.model.get_state() == Model.State.COMPRESSING:
            self.load_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'normal'
            self.compress_btn['state'] = 'disabled'
            self.save_btn['state'] = 'disabled'
            self.cancel_compress_btn['state'] = 'normal'
        elif self.model.get_state() == Model.State.COMPRESSED:
            self.load_btn['state'] = 'disabled'
            self.clear_btn['state'] = 'normal'
            self.compress_btn['state'] = 'disabled'
            self.save_btn['state'] = 'normal'
            self.cancel_compress_btn['state'] = 'normal'
        self.show()

    def show(self):
        if self.model.get_state() == Model.State.LOADED or self.model.get_state() == Model.State.COMPRESSING:
            self.convert_frame.grid(row=2, column=1, columnspan=3, state='LOADED')
        elif self.model.get_state() == Model.State.COMPRESSED:
            self.convert_frame.grid(row=2, column=1, columnspan=3, state='COMPRESSED')
        self.load_btn.grid(row=1, column=1)
        self.clear_btn.grid(row=3, column=1)
        self.compress_btn.grid(row=1, column=2)
        self.save_btn.grid(row=1, column=3)
        self.cancel_compress_btn.grid(row=3, column=3)
        self.Compress_ratio_text.grid(row=3, column=2)
        self.main_frame.mainloop()

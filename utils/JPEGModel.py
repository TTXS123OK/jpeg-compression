import numpy as np

from utils.ReadUtils import *
from utils.JPEGUtils import *
from typing import BinaryIO
from math import ceil
import matplotlib.pyplot as plt


class APP0:

    def __init__(self):
        self.segment_length = 0
        self.interchange_format = 0
        self.main_version_number = 0
        self.sub_version_number = 0
        self.density_unit = 0  # 0: 无单位; 1: 点数/英寸; 2: 点数/厘米
        self.X_density = 0
        self.Y_density = 0
        self.thumbnail_X = 0
        self.thumbnail_Y = 0

    def __str__(self):
        app0_info = ''
        app0_info += "segment_length: %d\n" % self.segment_length
        app0_info += "interchange_format: %s\n" % self.interchange_format
        app0_info += "main_version_number: %d\n" % self.main_version_number
        app0_info += "sub_version_number: %d\n" % self.sub_version_number
        app0_info += "density_unit: %d\n" % self.density_unit
        app0_info += "X_density: %d\n" % self.X_density
        app0_info += "Y_density: %d\n" % self.Y_density
        app0_info += "thumbnail_X: %d\n" % self.thumbnail_X
        app0_info += "thumbnail_Y: %d\n" % self.thumbnail_Y
        return app0_info

    def read(self, file: BinaryIO):
        """ Read APP marker """
        self.segment_length = read_word(file)
        self.interchange_format = file.read(5)
        self.main_version_number = read_byte(file)
        self.sub_version_number = read_byte(file)
        self.density_unit = read_byte(file)
        self.X_density = read_word(file)
        self.Y_density = read_word(file)
        self.thumbnail_X = read_byte(file)
        self.thumbnail_Y = read_byte(file)

        # 若存在缩略图，本实验中不做处理，直接跳过对应数据
        if self.thumbnail_X != 0 and self.thumbnail_Y != 0:
            file.seek(self.thumbnail_X * self.thumbnail_Y, 1)


class DQT:

    def __init__(self):
        self.segment_length = 0
        self.QT_information = 0
        self.QT = [[], []]

    def __str__(self):
        dqt_info = ''
        dqt_info += "segment_length: %d\n" % self.segment_length
        dqt_info += "QT_information: %d\n" % self.QT_information
        dqt_info += "QT: %s\n" % self.QT
        return dqt_info

    def read(self, file: BinaryIO):
        """ Read the quantization table. The table is in zigzag order """
        self.segment_length = read_word(file)
        i = 2
        while i < self.segment_length:
            self.QT_information = read_byte(file)
            i += 1
            # 4-7 bit: QT precision
            QT_precision = self.QT_information >> 4
            # 0-3 bit: QT number
            QT_number = self.QT_information & 0xF

            if QT_precision == 0:  # 精度为 8 bit
                for _ in range(64):
                    self.QT[QT_number].append(read_byte(file))
                i += 64
            else:
                for _ in range(64):
                    self.QT[QT_number].append(read_word(file))
                i += 64 * 2


class SOF0:

    def __init__(self):
        self.segment_length = 0
        self.sample_precision = 0
        self.height = 0
        self.weight = 0
        self.component_num = 0
        self.components = {}

    def __str__(self):
        sof0_info = ''
        sof0_info += "segment_length: %d\n" % self.segment_length
        sof0_info += "sample_precision: %d\n" % self.sample_precision
        sof0_info += "height: %d\n" % self.height
        sof0_info += "weight: %d\n" % self.weight
        sof0_info += "component_num: %d\n" % self.component_num
        sof0_info += "components: %s\n" % self.components
        return sof0_info

    def read(self, file: BinaryIO):
        """ Read the start of frame marker """
        self.segment_length = read_word(file)
        self.sample_precision = read_byte(file)
        self.height = read_word(file)
        self.weight = read_word(file)
        self.component_num = read_byte(file)
        for i in range(self.component_num):
            component_ID = read_byte(file)
            sample_coefficient = read_byte(file)
            QT_number = read_byte(file)
            self.components[component_ID] = {}
            self.components[component_ID]['sample_coefficient'] = sample_coefficient
            self.components[component_ID]['QT_number'] = QT_number


class DHT:

    def __init__(self):
        self.segment_length = 0
        self.HT_information = 0  # 0－3位:HT号; 4位:HT类型, 0＝DC表，1＝AC表; 5－7位：必须＝0
        self.HT_value_ac = [{}, {}]
        self.HT_value_dc = [{}, {}]

    def __str__(self):
        dht_info = ''
        dht_info += "segment_length: %d\n" % self.segment_length
        dht_info += "HT_information: %d\n" % self.HT_information
        dht_info += "HT_value_ac: %s\n" % self.HT_value_ac
        dht_info += "HT_value_dc: %s\n" % self.HT_value_dc
        return dht_info

    def read(self, file: BinaryIO):
        """ Read and compute the huffman tables """
        self.segment_length = read_word(file)
        i = 2
        while i < self.segment_length:  # one loop for one huffman table
            self.HT_information = read_byte(file)
            i += 1
            HT_number = self.HT_information & 0x0f
            if HT_number > 2:
                raise IndexError("Unexpected HT number")
            HT_type = self.HT_information >> 4
            huff_symbol_cnt_for_each_len = []
            huff_symbol = []
            # 不同长度（1-16）的huffman编码的个数
            huff_symbol_num = 0
            for _ in range(16):
                num = read_byte(file)
                huff_symbol_cnt_for_each_len.append(num)
                huff_symbol_num += num
            i += 16
            for _ in range(huff_symbol_num):
                huff_symbol.append(read_byte(file))
            i += huff_symbol_num
            if HT_type == 0:
                self.HT_value_dc[HT_number] = self.map_huff_symbol(huff_symbol_cnt_for_each_len, huff_symbol)
            else:
                self.HT_value_ac[HT_number] = self.map_huff_symbol(huff_symbol_cnt_for_each_len, huff_symbol)

    def map_huff_symbol(self, huff_symbol_cnt_for_each_len: list[int], huff_symbol: list[int]) \
            -> dict[tuple[int, str], int]:
        cur_symbol_idx = 0
        table = {}
        cur_code = 0
        for i in range(len(huff_symbol_cnt_for_each_len)):
            cnt = huff_symbol_cnt_for_each_len[i]
            n_bits = i + 1
            for _ in range(cnt):
                code_str = str(bin(cur_code)).split('b')[1]
                huff_code = (n_bits, '0' * (n_bits - len(code_str)) + code_str)
                table[huff_code] = huff_symbol[cur_symbol_idx]
                cur_code += 1
                cur_symbol_idx += 1
            cur_code <<= 1
        return table


class SOS:

    def __init__(self):
        self.segment_length = 0
        self.component_num = 0
        self.components = {}

    def __str__(self):
        sos_info = ''
        sos_info += "segment_length: %d\n" % self.segment_length
        sos_info += "component_num: %d\n" % self.component_num
        sos_info += "components: %s\n" % self.components

    def read(self, file: BinaryIO):
        """ Read the start of scan marker """
        self.segment_length = read_word(file)
        self.component_num = read_byte(file)

        for _ in range(self.component_num):
            component_ID = read_byte(file)
            HT_number = read_byte(file)
            self.components[component_ID] = {}
            self.components[component_ID]['HT_number'] = HT_number
        read_byte(file)
        read_byte(file)
        read_byte(file)


class JPEG:

    def __init__(self, app0: APP0 = APP0(), dqt: DQT = DQT(), sof0: SOF0 = SOF0(), dht: DHT = DHT(), sos: SOS = SOS()):
        self.app0 = app0
        self.dqt = dqt
        self.sof0 = sof0
        self.dht = dht
        self.sos = sos
        self.mcu_list = []

    def __str__(self):
        jpeg_info = ''
        jpeg_info += "app0: \n%s\n" % self.app0
        jpeg_info += "dqt: \n%s\n" % self.dqt
        jpeg_info += "sof0: %s\n" % self.sof0
        jpeg_info += "dht: %s\n" % self.dht
        jpeg_info += "sos: %s\n" % self.sos
        return jpeg_info

    def get_dc_table(self, idx: int):
        return self.dht.HT_value_dc[idx]

    def get_ac_table(self, idx: int):
        return self.dht.HT_value_ac[idx]

    def get_component_num(self):
        return self.sos.component_num

    def get_component_factor(self, idx: int):
        coefficient = self.sof0.components[idx]["sample_coefficient"]
        return coefficient >> 4, coefficient & 0xF

    def get_component_HT_number(self, idx: int):
        HT_number = self.sos.components[idx]['HT_number']
        return HT_number >> 4, HT_number & 0xF

    def get_qtable(self, idx: int):
        return self.dqt.QT[idx]

    def get_component_qt_number(self, idx: int):
        return self.sof0.components[idx]['QT_number']

    def get_size(self) -> tuple[int, int]:
        return self.sof0.height, self.sof0.weight

    def read(self, file: BinaryIO):
        data_stream = jpeg_bit_reader(file)
        try:
            while True:
                cmd = data_stream.__next__()
                if isinstance(cmd, JpegCommand):
                    if cmd == JpegCommand.read_app0:
                        self.app0.read(file)
                    elif cmd == JpegCommand.read_dqt:
                        self.dqt.read(file)
                    elif cmd == JpegCommand.read_sof0:
                        self.sof0.read(file)
                    elif cmd == JpegCommand.read_dht:
                        self.dht.read(file)
                    elif cmd == JpegCommand.read_sos:
                        self.sos.read(file)
                        self.read_mcu_list(data_stream)
                    elif cmd == JpegCommand.read_stop:
                        return
                    else:
                        raise TypeError("Unknown jpeg read command")
        except StopIteration:
            return

    def read_mcu_list(self, data_stream: Generator[Union[int, JpegCommand], None, None]):
        mcu = self.read_mcu(data_stream)
        while mcu is not None:
            self.mcu_list.append(mcu)
            mcu = self.read_mcu(data_stream)

    def read_mcu(self, data_stream: Generator[Union[int, JpegCommand], None, None]) -> Union[list[list[list[int]]], None]:
        mcu = []
        # for each component
        for i in range(self.get_component_num()):
            mcu_comp = []
            comp_id = i + 1
            horizontal_factor, vertical_factor = jpeg.get_component_factor(comp_id)
            for j in range(horizontal_factor * vertical_factor):
                data_unit = self.read_data_unit(data_stream, comp_id)
                if data_unit is None:
                    if i == 0 and j == 0:
                        return None
                    else:
                        raise AssertionError("Read MCU failed")
                mcu_comp.append(data_unit)
            mcu.append(mcu_comp)
        return mcu

    def read_data_unit(
            self,
            data_stream: Generator[Union[int, JpegCommand], None, None],
            comp_id: int
    ) -> Union[list[int], None]:
        data_unit = []
        HT_dc_number, HT_ac_number = self.get_component_HT_number(comp_id)
        dc_huff_table = self.get_dc_table(HT_dc_number)
        ac_huff_table = self.get_ac_table(HT_ac_number)

        while len(data_unit) < 64:
            # parse dc value
            if len(data_unit) == 0:
                try:
                    key_str = ''
                    while len(key_str) < 16:
                        bit = data_stream.__next__()
                        key_str += str(bit)
                        if (len(key_str), key_str) in dc_huff_table:
                            size = dc_huff_table[(len(key_str), key_str)]
                            if size == 0:  # means amplitude is 0
                                data_unit.append(0)
                                break
                            amplitude = read_amplitude(size, data_stream)
                            data_unit.append(amplitude)
                            break
                        else:
                            if len(key_str) == 16:
                                raise AssertionError("Parse DC value failed")
                except StopIteration:
                    return None

            # parse ac value
            else:
                val = 0
                key_str = ''
                while len(key_str) < 16:
                    bit = data_stream.__next__()
                    key_str += str(bit)
                    if (len(key_str), key_str) in ac_huff_table:
                        val = ac_huff_table[(len(key_str), key_str)]
                        break
                    else:
                        if len(key_str) == 16:
                            raise AssertionError("Parse AC value failed")

                # symbol1: (RUNLENGTH, SIZE)
                # symbol2: (AMPLITUDE)
                if val == 0x00:  # fill all zero to data_unit
                    data_unit.extend([0] * (64-len(data_unit)))
                elif val == 0xF0:  # fill with 16 zero coefficients
                    data_unit.extend([0] * 16)
                elif val & 0x0f == 0:  # SIZE can not be 0
                    raise AssertionError("SIZE can not be 0 in RLC")
                else:
                    run_length = val >> 4
                    data_unit.extend([0] * run_length)
                    size = val & 0x0f
                    amplitude = read_amplitude(size, data_stream)
                    data_unit.append(amplitude)

        return data_unit

    def decompress_to_rgb(self) -> list[list[list[int]]]:
        ycbcr_mcu_list = self.mcu_list.copy()
        recover_dc(ycbcr_mcu_list)
        for mcu in ycbcr_mcu_list:
            for idx, comp in enumerate(mcu):
                comp_id = idx + 1
                qt_number = self.get_component_qt_number(comp_id)
                qtable = self.get_qtable(qt_number)
                for i in range(len(comp)):
                    dequantization(comp[i], qtable)
                    comp[i] = inv_zigzag(comp[i])
                    comp[i] = IDCT(comp[i], idct_table)

        height, width = self.get_size()
        ycbcr = [[[] for y in range(width)] for x in range(height)]
        component_num = self.get_component_num()
        mcu_h, mcu_w = 0, 0
        for k in range(component_num):
            comp_id = k + 1
            horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
            mcu_h = max(mcu_h, vertical_factor * 8)
            mcu_w = max(mcu_w, horizontal_factor * 8)
        for k in range(component_num):
            comp_id = k + 1
            horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
            mcu_cnt_each_row = ceil(width / mcu_w)
            for i in range(height):
                y = i // mcu_h
                y_offset_in_mcu = i % mcu_h
                y_offset_in_du = (y_offset_in_mcu % (mcu_h // vertical_factor)) // (mcu_h // (8 * vertical_factor))
                for j in range(width):
                    x = j // mcu_w
                    x_offset_in_mcu = j % mcu_w
                    x_offset_in_du = (x_offset_in_mcu % (mcu_h // horizontal_factor)) // (mcu_w // (8 * horizontal_factor))
                    mcu_idx = x + y * mcu_cnt_each_row
                    data_unit_idx = y_offset_in_mcu // (mcu_h // horizontal_factor) * horizontal_factor \
                                    + x_offset_in_mcu // (mcu_w // vertical_factor)
                    ycbcr[i][j].append(ycbcr_mcu_list[mcu_idx][k][data_unit_idx][y_offset_in_du][x_offset_in_du])

        rgb = [[] for x in range(height)]
        for i in range(height):
            for j in range(width):
                rgb[i].append(YCbCr2RGB(ycbcr[i][j]))
        return rgb


def displayImage(image):
    plt.imshow(image)
    plt.show()


if __name__ == '__main__':
    jpeg = JPEG()
    file_path = "../simplified-jpeg-demo/assets/warma.jpg"
    with open(file_path, 'rb') as f:
        jpeg.read(f)
    rgb = jpeg.decompress_to_rgb()
    displayImage(rgb)

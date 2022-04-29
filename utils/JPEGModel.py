import numpy as np
from utils.WriteUtils import *
from utils.ReadUtils import *
from utils.JPEGUtils import *
from typing import BinaryIO
from math import ceil
import matplotlib.pyplot as plt


class APP0:

    def __init__(self):
        self.segment_length = 0
        self.interchange_format: str = ""
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

    def set(self):
        self.segment_length = 16
        self.interchange_format = "JFIF\0"
        self.main_version_number = 1
        self.sub_version_number = 1
        self.density_unit = 1
        self.X_density = 96
        self.Y_density = 96
        self.thumbnail_X = 0
        self.thumbnail_Y = 0

    def write(self, file: BinaryIO):
        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xe0)
        write_bytes(file, 2, self.segment_length)
        write_str(file, self.interchange_format)
        write_bytes(file, 1, self.main_version_number)
        write_bytes(file, 1, self.sub_version_number)
        write_bytes(file, 1, self.density_unit)
        write_bytes(file, 2, self.X_density)
        write_bytes(file, 2, self.Y_density)
        write_bytes(file, 1, self.thumbnail_X)
        write_bytes(file, 1, self.thumbnail_Y)


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

    def set(self):
        self.QT = [
            # QT for Y
            [
                3, 2, 2, 3, 2, 2, 3, 3,
                3, 3, 4, 3, 3, 4, 5, 8,
                5, 5, 4, 4, 5, 10, 7, 7,
                6, 8, 12, 10, 12, 12, 11, 10,
                11, 11, 13, 14, 18, 16, 13, 14,
                17, 14, 11, 11, 16, 22, 16, 17,
                19, 20, 21, 21, 21, 12, 15, 23,
                24, 22, 20, 24, 18, 20, 21, 20
            ],
            # QT for Cb, Cr
            [
                3, 4, 4, 5, 4, 5, 9, 5,
                5, 9, 20, 13, 11, 13, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20,
                20, 20, 20, 20, 20, 20, 20, 20
            ]
        ]

    def write(self, file: BinaryIO):
        for idx, qt in enumerate(self.QT):
            write_bytes(file, 1, 0xff)
            write_bytes(file, 1, 0xdb)

            segment_length = 67
            precision = 0
            info = (precision << 4) | (idx & 0xf)

            write_bytes(file, 2, segment_length)
            write_bytes(file, 1, info)

            for coef in qt:
                write_bytes(file, 1, coef)


class SOF0:

    def __init__(self):
        self.segment_length = 0
        self.sample_precision = 0
        self.height = 0
        self.width = 0
        self.component_num = 0
        self.components = {}

    def __str__(self):
        sof0_info = ''
        sof0_info += "segment_length: %d\n" % self.segment_length
        sof0_info += "sample_precision: %d\n" % self.sample_precision
        sof0_info += "height: %d\n" % self.height
        sof0_info += "width: %d\n" % self.width
        sof0_info += "component_num: %d\n" % self.component_num
        sof0_info += "components: %s\n" % self.components
        return sof0_info

    def read(self, file: BinaryIO):
        """ Read the start of frame marker """
        self.segment_length = read_word(file)
        self.sample_precision = read_byte(file)
        self.height = read_word(file)
        self.width = read_word(file)
        self.component_num = read_byte(file)
        for i in range(self.component_num):
            component_ID = read_byte(file)
            sample_coefficient = read_byte(file)
            QT_number = read_byte(file)
            self.components[component_ID] = {}
            self.components[component_ID]['sample_coefficient'] = sample_coefficient
            self.components[component_ID]['QT_number'] = QT_number

    def set(self):
        self.segment_length = 17
        self.sample_precision = 8
        self.component_num = 3
        self.components = {
            1: {'sample_coefficient': 0x22, 'QT_number': 0},
            2: {'sample_coefficient': 0x11, 'QT_number': 1},
            3: {'sample_coefficient': 0x11, 'QT_number': 1}
        }

    def write(self, file: BinaryIO):
        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xc0)
        write_bytes(file, 2, self.segment_length)
        write_bytes(file, 1, self.sample_precision)
        write_bytes(file, 2, self.height)
        write_bytes(file, 2, self.width)
        write_bytes(file, 1, self.component_num)
        for key, item in self.components.items():
            write_bytes(file, 1, key)
            write_bytes(file, 1, item['sample_coefficient'])
            write_bytes(file, 1, item['QT_number'])


class DHT:

    def __init__(self):
        self.segment_length = 0
        self.HT_information = 0  # 0－3位:HT号; 4位:HT类型, 0＝DC表，1＝AC表; 5－7位：必须＝0
        self.dc_tables = [[], []]
        self.ac_tables = [[], []]
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
                self.HT_value_dc[HT_number] = map_huff_symbol(huff_symbol_cnt_for_each_len, huff_symbol)
            else:
                self.HT_value_ac[HT_number] = map_huff_symbol(huff_symbol_cnt_for_each_len, huff_symbol)

    def set(self, mcu_list: list[list[list[list[int]]]]):
        self.dc_tables = create_dc_huffman_tables(mcu_list)
        self.ac_tables = create_ac_huffman_tables(mcu_list)

    def write(self, file: BinaryIO):
        for idx, table in enumerate(self.dc_tables):
            self.write_huffman_table(file, 0, idx, table)
        for idx, table in enumerate(self.ac_tables):
            self.write_huffman_table(file, 1, idx, table)

    def write_huffman_table(self, file: BinaryIO, tbl_type: int, tbl_idx: int, huffman_table: list[list[int], list[int]]):
        symbol_cnt_for_each_len = huffman_table[0]
        symbols = huffman_table[1]
        segment_length = 2 + 1 + len(symbol_cnt_for_each_len) + len(symbols)
        HT_info = tbl_type << 4 | tbl_idx

        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xc4)
        write_bytes(file, 2, segment_length)
        write_bytes(file, 1, HT_info)
        for cnt in symbol_cnt_for_each_len:
            write_bytes(file, 1, cnt)
        for symbol in symbols:
            write_bytes(file, 1, symbol)


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
        return sos_info

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

    def set(self):
        self.segment_length = 12
        self.component_num = 3
        self.components = {
            1: {'HT_number': 0x00},
            2: {'HT_number': 0x11},
            3: {'HT_number': 0x11}
        }

    def write(self, file: BinaryIO):
        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xda)
        write_bytes(file, 2, self.segment_length)
        write_bytes(file, 1, self.component_num)
        for comp_id, info in self.components.items():
            write_bytes(file, 1, comp_id)
            write_bytes(file, 1, info['HT_number'])
        write_bytes(file, 1, 0x00)
        write_bytes(file, 1, 0x3f)
        write_bytes(file, 1, 0x00)


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
        return self.sof0.height, self.sof0.width

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
        self.mcu_list = []
        mcu_num = ceil(self.sof0.height / 16) * ceil(self.sof0.width / 16)
        while len(self.mcu_list) < mcu_num:
            mcu = self.read_mcu(data_stream)
            if mcu is not None:
                self.mcu_list.append(mcu)
            else:
                break

        # mcu = self.read_mcu(data_stream)
        # while mcu is not None:
        #     self.mcu_list.append(mcu)
        #     mcu = self.read_mcu(data_stream)

    def read_mcu(self, data_stream: Generator[Union[int, JpegCommand], None, None]) -> Union[
        list[list[list[int]]], None]:
        mcu = []
        # for each component
        for i in range(self.get_component_num()):
            mcu_comp = []
            comp_id = i + 1
            horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
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
                except Exception:
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
                    data_unit.extend([0] * (64 - len(data_unit)))
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

        # print(ycbcr_mcu_list[0])
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
                    x_offset_in_du = (x_offset_in_mcu % (mcu_h // horizontal_factor)) // (
                            mcu_w // (8 * horizontal_factor))
                    mcu_idx = x + y * mcu_cnt_each_row
                    data_unit_idx = y_offset_in_mcu // (mcu_h // horizontal_factor) * horizontal_factor \
                                    + x_offset_in_mcu // (mcu_w // vertical_factor)
                    ycbcr[i][j].append(ycbcr_mcu_list[mcu_idx][k][data_unit_idx][y_offset_in_du][x_offset_in_du])

        rgb = [[] for x in range(height)]
        for i in range(height):
            for j in range(width):
                rgb[i].append(YCbCr2RGB(ycbcr[i][j]))
        return rgb

    def compress_from_rgb(self, rgb: list[list[tuple[int]]]):

        self.app0.set()
        self.dqt.set()
        self.sof0.set()
        self.sos.set()

        height = len(rgb)
        width = len(rgb[0])

        self.sof0.height = height
        self.sof0.width = width

        ycbcr = []
        for i in range(height):
            row = []
            for j in range(width):
                row.append(RGB2YCbCr(rgb[i][j]))
            ycbcr.append(row)

        mcu_list = self.divide_into_mcu_list(ycbcr)
        self.subsampling(mcu_list)

        for mcu in mcu_list:
            for idx, comp in enumerate(mcu):
                comp_id = idx + 1
                qt_number = self.get_component_qt_number(comp_id)
                qtable = self.get_qtable(qt_number)
                for data_unit_idx, data_unit in enumerate(comp):
                    data_unit = DCT(data_unit, dct_table)
                    comp[data_unit_idx] = zigzag(data_unit)
                    quantization(comp[data_unit_idx], qtable)

        # current mcu_list:
        # mcu: list of components
        # component: list of data_units
        # data_unit: array of 64 coefficients
        dpcm_on_dc(mcu_list)
        self.mcu_list = mcu_list

    # mcu_list: list of mcus
    # mcu: list of components
    # components: only one 16x16 block there
    # block: 16x16 matrix
    def divide_into_mcu_list(self, ycbcr: list[list[list[int]]]) -> list[list[list[list[list[int]]]]]:
        height = len(ycbcr)
        width = len(ycbcr[0])

        max_horizontal_factor, max_vertical_factor = 0, 0
        for idx in range(self.get_component_num()):
            comp_id = idx + 1
            horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
            max_horizontal_factor = max(max_horizontal_factor, horizontal_factor)
            max_vertical_factor = max(max_vertical_factor, vertical_factor)
        mcu_height = 8 * max_vertical_factor
        mcu_width = 8 * max_horizontal_factor
        mcu_col_cnt = ceil(height / mcu_height)
        mcu_row_cnt = ceil(width / mcu_width)
        mcu_list = []
        for mcu_idx in range(mcu_row_cnt * mcu_col_cnt):
            mcu_x_offset = (mcu_idx % mcu_row_cnt) * mcu_width
            mcu_y_offset = (mcu_idx // mcu_row_cnt) * mcu_height
            mcu = []
            for comp_idx in range(self.get_component_num()):
                comp = []
                block = []
                for i in range(mcu_height):
                    row = []
                    for j in range(mcu_width):
                        if mcu_y_offset + i >= height or mcu_x_offset + j >= width:
                            row.append(0)
                        else:
                            row.append(ycbcr[mcu_y_offset + i][mcu_x_offset + j][comp_idx])
                    block.append(row)
                comp.append(block)
                mcu.append(comp)
            mcu_list.append(mcu)
        return mcu_list

    def subsampling(self, mcu_list: list[list[list[list[list[int]]]]]) -> None:
        max_horizontal_factor, max_vertical_factor = 0, 0
        for idx in range(self.get_component_num()):
            comp_id = idx + 1
            horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
            max_horizontal_factor = max(max_horizontal_factor, horizontal_factor)
            max_vertical_factor = max(max_vertical_factor, vertical_factor)

        for mcu in mcu_list:
            for idx, comp in enumerate(mcu):
                comp_id = idx + 1
                horizontal_factor, vertical_factor = self.get_component_factor(comp_id)
                subsample_x_factor = max_horizontal_factor // horizontal_factor
                subsample_y_factor = max_vertical_factor // vertical_factor

                new_comp = []
                for du_idx in range(vertical_factor * horizontal_factor):
                    du_x_offset = (du_idx % horizontal_factor) * 8 * subsample_x_factor
                    du_y_offset = (du_idx // horizontal_factor) * 8 * subsample_y_factor
                    data_unit = []
                    for i in range(8):
                        row = []
                        for j in range(8):
                            s = 0
                            for x in range(subsample_x_factor):
                                for y in range(subsample_y_factor):
                                    s += comp[0][du_y_offset + i * subsample_y_factor + y][
                                        du_x_offset + j * subsample_x_factor + x]
                            row.append(s // (subsample_x_factor * subsample_y_factor))
                        data_unit.append(row)
                    new_comp.append(data_unit)
                mcu[idx] = new_comp

    def write(self, file: BinaryIO):
        self.dht.set(self.mcu_list)
        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xd8)
        self.app0.write(file)
        self.dqt.write(file)
        self.sof0.write(file)
        self.dht.write(file)
        self.sos.write(file)
        writer = BitWriter(file)
        Y_dc_map = map_symbol_to_coding(self.dht.dc_tables[0][0], self.dht.dc_tables[0][1])
        CbCr_dc_map = map_symbol_to_coding(self.dht.dc_tables[1][0], self.dht.dc_tables[1][1])
        Y_ac_map = map_symbol_to_coding(self.dht.ac_tables[0][0], self.dht.ac_tables[0][1])
        CbCr_ac_map = map_symbol_to_coding(self.dht.ac_tables[1][0], self.dht.ac_tables[1][1])
        for mcu in self.mcu_list:
            for idx, comp in enumerate(mcu):
                comp_id = idx + 1
                for data_unit in comp:
                    symbol = 0 if data_unit[0] == 0 else get_value_bit_len(data_unit[0])  # write dc
                    if comp_id == 1:
                        writer.write(Y_dc_map[symbol])
                    else:
                        writer.write(CbCr_dc_map[symbol])
                    if symbol > 0:
                        writer.write(get_complement_code(data_unit[0]))

                    i = 1  # write ac
                    last_nonzero_idx = 64
                    while last_nonzero_idx > 0 and data_unit[last_nonzero_idx-1] == 0:
                        last_nonzero_idx -= 1
                    zero_cnt = 0
                    while i < last_nonzero_idx:
                        if data_unit[i] == 0:
                            zero_cnt += 1
                            if zero_cnt == 16:  # special case
                                symbol = 0xf0
                                zero_cnt = 0
                                if comp_id == 1:
                                    writer.write(Y_ac_map[symbol])
                                else:
                                    writer.write(CbCr_ac_map[symbol])
                        else:
                            amplitude = data_unit[i]
                            size = get_value_bit_len(amplitude)
                            symbol = zero_cnt << 4 | size
                            zero_cnt = 0
                            if comp_id == 1:
                                writer.write(Y_ac_map[symbol])
                            else:
                                writer.write(CbCr_ac_map[symbol])
                            writer.write(get_complement_code(amplitude))
                        i += 1
                    if last_nonzero_idx < 64:
                        symbol = 0
                        if comp_id == 1:
                            writer.write(Y_ac_map[symbol])
                        else:
                            writer.write(CbCr_ac_map[symbol])
        writer.stop()
        write_bytes(file, 1, 0xff)
        write_bytes(file, 1, 0xd9)


def displayImage(image):
    plt.imshow(image)
    plt.show()


if __name__ == '__main__':
    jpeg = JPEG()
    path1 = "assets/red.jpg"
    path2 = "assets/warma.jpg"
    path3 = "assets/tmp.jpeg"
    with open(path2, 'rb') as f:
        jpeg.read(f)

    # print(jpeg)

    rgb1 = jpeg.decompress_to_rgb()  # this will change data_unit into 8 x 8
    displayImage(rgb1)
    jpeg.compress_from_rgb(rgb1)  # recover data_unit to list of 64

    with open(path3, 'wb') as f2:
        jpeg.write(f2)
    with open(path3, 'rb') as f:
        jpeg.read(f)

    rgb1 = jpeg.decompress_to_rgb()  # this will change data_unit into 8 x 8
    displayImage(rgb1)

    # jpeg.compress_from_rgb(rgb1)  # recover data_unit to list of 64
    # rgb2 = jpeg.decompress_to_rgb()  # this will change data_unit into 8 x 8
    # displayImage(rgb2)

    # print(jpeg)
    # print(jpeg.mcu_list)

    # rgb1 = jpeg.decompress_to_rgb()
    # jpeg.compress_from_rgb(rgb1)
    # rgb2 = jpeg.decompress_to_rgb()
    #
    # print(rgb1[0])
    # print(rgb2[0])

    # with open(path3, 'wb') as f2:
    #     jpeg.write(f2)

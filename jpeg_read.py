import sys
from math import *
from JPEG import *

data = []


def read_word(file):
    """ Read a 2 byte word from file """
    out = file.read(2)
    out = out[0] << 8 | out[1]
    return out


def read_byte(file):
    """ Read a byte from file """
    out = 0
    input = file.read(1)
    if input:
        out = ord(input)
    return out


def read_app(APP, type, file):
    """ Read APP marker """
    APP.segment_length = read_word(file)

    if type == 0:
        APP.interchange_format = file.read(5)
        APP.main_version_number = read_byte(file)
        APP.sub_version_number = read_byte(file)
        APP.density_unit = read_byte(file)
        APP.X_density = read_word(file)
        APP.Y_density = read_word(file)
        APP.thumbnail_X = read_byte(file)
        APP.thumbnail_Y = read_byte(file)

        # 存在缩略图，但是本实验中不做处理，直接跳过对应数据
        if APP.thumbnail_X != 0 and APP.thumbnail_Y != 0:
            file.seek(APP.thumbnail_X * APP.thumbnail_Y, 1)


def read_dqt(DQT, file):
    """ Read the quantization table.
        The table is in zigzag order """

    DQT.segment_length = read_word(file)
    i = 2
    while i < DQT.segment_length:
        DQT.QT_information = read_byte(file)
        # 4-7 bit: QT precision
        QT_precision = DQT.QT_information >> 4
        # 0-3 bit: QT number
        QT_number = DQT.QT_information & 0xF
        i += 1
        if QT_precision == 0:  # 精度为 8 bit
            for j in range(64):
                DQT.QT[QT_number].append(read_byte(file))
            i += 64
        else:
            for j in range(64):
                DQT.QT[QT_number].append(read_word(file))
            i += 64 * 2


def read_sof(SOF, type, file):
    """ Read the start of frame marker """

    if type == 0:
        SOF.segment_length = read_word(file)
        SOF.sample_precision = read_byte(file)
        SOF.height = read_word(file)
        SOF.weight = read_word(file)
        SOF.component_num = read_byte(file)
        for i in range(SOF.component_num):
            component_ID = read_byte(file)
            sample_coefficient = read_byte(file)
            QT_number = read_byte(file)
            SOF.components[component_ID] = {}
            SOF.components[component_ID]['sample_coefficient'] = sample_coefficient
            SOF.components[component_ID]['QT_number'] = QT_number


def read_dht(DHT, file):
    """ Read and compute the huffman tables """
    # Read the marker length
    DHT.segment_length = read_word(file)
    i = 2
    while i < DHT.segment_length:
        DHT.HT_information = read_byte(file)
        i += 1
        HT_number = DHT.HT_information & 0x0F
        HT_type = (DHT.HT_information >> 4) & 0x0F
        huff_length_count = []
        huff_symbol = []
        # 不同长度（1-16）的huffman编码的个数
        huff_num = 0
        for j in range(16):
            num = read_byte(file)
            huff_length_count.append(num)
            huff_num += num
        i += 16
        for j in range(huff_num):
            huff_symbol.append(read_byte(file))
        i += huff_num
        if HT_type == 0:
            DHT.HT_value_dc[HT_number] = huffman_map(huff_length_count, huff_symbol)
        else:
            DHT.HT_value_ac[HT_number] = huffman_map(huff_length_count, huff_symbol)


def huffman_map(huff_length_count, huff_symbol):
    cur_symbol_index = 0
    table = {}
    cur_code = 0
    for i in range(len(huff_length_count)):
        count = huff_length_count[i]
        n_bits = i + 1
        for j in range(count):
            code_str = str(bin(cur_code)).split('b')[1]
            huffman_code = (n_bits, '0' * (n_bits - len(code_str)) + code_str)
            table[huffman_code] = huff_symbol[cur_symbol_index]
            cur_code += 1
            cur_symbol_index += 1
        cur_code <<= 1
    return table


def read_sos(SOS, file):
    """ Read the start of scan marker """

    SOS.segment_length = read_word(file)
    SOS.component_num = read_byte(file)

    for i in range(SOS.component_num):
        component_ID = read_byte(file)
        HT_number = read_byte(file)
        SOS.components[component_ID] = {}
        SOS.components[component_ID]['HT_number'] = HT_number
    read_byte(file)
    read_byte(file)
    read_byte(file)


def read_bits(jpeg, file):
    input = read_byte(file)
    while not jpeg.EOI:
        # print("input:%x" % input)
        if input == 0xFF:
            cmd = read_byte(file)
            # print("cmd:%x" % cmd)
            # Byte stuffing
            if cmd == 0x00:
                input = 0xFF
            # End of image marker
            elif cmd == 0xD9:
                jpeg.EOI = True
            # Restart markers
            elif 0xD0 <= cmd <= 0xD7:
                # Reset dc value
                jpeg.dc = [0 for i in range(jpeg.get_num_component() + 1)]
                input = read_byte(file)
            else:
                input = read_byte(file)

        if not jpeg.EOI:
            for i in range(7, -1, -1):
                # Output next bit
                # print((input >> i) & 0x01)
                yield (input >> i) & 0x01

            input = read_byte(file)
    while True:
        yield []


def read_mcu(jpeg):
    """ Read an MCU """

    mcu = [[] for i in range(jpeg.get_component_num())]

    # For each component
    for i in range(jpeg.get_component_num()):
        mcu[i] = []
        # For each DU
        sample_height, sample_weight = jpeg.get_component_size(i + 1)
        for j in range(sample_height * sample_weight):
            DU = read_data_unit(jpeg, i + 1)
            if not jpeg.EOI:
                mcu[i].append(DU)

    if mcu != [[] for i in range(jpeg.get_component_num())]:
        jpeg.MCU.append(mcu)


def read_data_unit(jpeg, comp_id):
    """ Read one DU with component id """
    key_len = []
    data = []

    HT_dc_number, HT_ac_number = jpeg.get_component_HT_number(comp_id)
    HT = jpeg.get_dc_table(HT_dc_number)

    # Fill data with 64 coefficients
    while len(data) < 64:
        key = 0

        for bits in range(1, 17):
            key_len = []
            key <<= 1
            # Get one bit from bit_stream
            val = get_bits(1, jpeg.data_stream)
            if val == []:
                break
            key |= val
            # print((bits, str(bin(key)).split('b')[1]))
            # If huffman code exists
            key_str = '0' * (bits - len(str(bin(key)).split('b')[1])) + str(bin(key)).split('b')[1]
            if (bits, key_str) in HT:
                # print("yes")
                key_len = HT[(bits, key_str)]
                # print(key_len)
                break

        # After getting the DC value, switch to the AC table
        HT = jpeg.get_ac_table(HT_ac_number)
        # If huffman code doesn't exist
        if key_len == []:
            break
        # If ZRL fill with 16 zero coefficients
        elif key_len == 0xF0:
            for i in range(16):
                data.append(0)
            continue

        # If not DC coefficient
        if len(data) != 0:
            # If End of block
            if key_len == 0x00:
                # Fill the rest of the DU with zeros
                while len(data) < 64:
                    data.append(0)
                break

            # The first part of the AC key_len is the number of leading zeros
            for i in range(key_len >> 4):
                if len(data) < 64:
                    data.append(0)
            key_len &= 0x0F

        if len(data) >= 64:
            break

        if key_len != 0:
            # The rest of key_len is the amount of "additional" bits
            val = get_bits(key_len, jpeg.data_stream)
            if val == []:
                break
            # Decode the additional bits
            num = calc_bits(key_len, val)

            data.append(num)
        else:
            data.append(0)

    return data


def get_bits(num, gen):
    """ Get "num" bits from gen """
    out = 0
    for i in range(num):
        out <<= 1
        val = gen.__next__()
        # print(val)
        if val != []:
            out += val & 0x01
        else:
            return []

    return out


def calc_bits(len, val):
    """ Calculate the value from the "additional" bits in the huffman data. """
    if val & (1 << len - 1):
        pass
    else:
        val -= (1 << len) - 1
    return val


def recover_dc(jpeg):
    """recover dc value using dc value from previous MCU"""
    for mcu in jpeg.MCU:
        for comp in range(len(mcu)):
            for du in range(len(mcu[comp])):
                if mcu[comp][du]:
                    mcu[comp][du][0] += jpeg.dc[comp]
                    jpeg.dc[comp] = mcu[comp][du][0]


input_filename = 'warma.jpg'
jpeg_file = open(input_filename, "rb")

jpeg = JPEG()

in_char = read_byte(jpeg_file)

while in_char:
    if in_char == 0xff:
        in_num = read_byte(jpeg_file)
        # print("FF%02X" % in_num)
        if in_num == 0xd8:
            """读取到文件头"""
            # print("SOI")
        elif 0xd0 <= in_num <= 0xd7:
            """RST标记，复位标记"""
            # print("RST%x" % (in_num - 0xd0))
        elif 0xe0 <= in_num <= 0xef:
            """读取到图像识别信息"""
            # print("APP%x" % (in_num - 0xe0))
            read_app(jpeg.APP0, in_num - 0xe0, jpeg_file)
        elif in_num == 0xdb:
            """读取到量化表"""
            # print("DQT")
            read_dqt(jpeg.DQT, jpeg_file)
        elif in_num == 0xc0:
            """读取到图像基本信息"""
            # print("SOF%x" % (in_num - 0xc0))
            read_sof(jpeg.SOF0, in_num - 0xc0, jpeg_file)
        elif in_num == 0xc4:
            """读取到huffman表"""
            # print("DHT")
            read_dht(jpeg.DHT, jpeg_file)
        elif in_num == 0xda:
            """读取到扫描行开始"""
            # print("SOS")
            read_sos(jpeg.SOS, jpeg_file)
            jpeg.dc = [0 for i in range(jpeg.get_component_num() + 1)]
            jpeg.data_stream = read_bits(jpeg, jpeg_file)
            while not jpeg.EOI:
                read_mcu(jpeg)
        elif in_num == 0xd9:
            """读取到文件尾"""
            # print("EOI")

    in_char = read_byte(jpeg_file)

jpeg_file.close()

recover_dc(jpeg)

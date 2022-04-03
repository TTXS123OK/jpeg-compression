import sys
from math import *
from JPEG import *


def read_word(file):
    """ Read a 2 byte word from file """
    out = file.read(2)
    out = out[0] << 8 | out[1]
    return out


def read_byte(file):
    """ Read a byte from file """
    out = ord(file.read(1))
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
        if QT_precision == 0:   # 精度为 8 bit
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
            DHT.HT_value_dc[HT_number] = huffman_decode(huff_length_count, huff_symbol)
        else:
            DHT.HT_value_ac[HT_number] = huffman_decode(huff_length_count, huff_symbol)


def huffman_decode(huff_length_count, huff_symbol):
    cur_symbol_index = 0
    table = {}
    cur_code = 0
    for i in range(len(huff_length_count)):
        count = huff_length_count[i]
        n_bits = i + 1
        for j in range(count):
            code_str = str(bin(cur_code)).split('b')[1]
            huffman_code = '0' * (n_bits - len(code_str)) + code_str
            table[huff_symbol[cur_symbol_index]] = huffman_code
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
        SOS.component[component_ID]['HT_number'] = HT_number


#
# # def read_dnl(file):
# #     """Read the DNL marker Changes the number of lines """
# #     global XYP
# #
# #     Ld = read_word(file)
# #     Ld -= 2
# #     NL = read_word(file)
# #     Ld -= 2
# #
# #     X, Y, P = XYP
# #
# #     if Y == 0:
# #         XYP = X, NL, P
#
#
#
# def calc_add_bits(len, val):
#     """ Calculate the value from the "additional" bits in the huffman data. """
#     if (val & (1 << len - 1)):
#         pass
#     else:
#         val -= (1 << len) - 1
#
#     return val
#
#
# def bit_read(file):
#     """ Read one bit from file and handle markers and byte stuffing This is a generator function, google it. """
#     global EOI
#     global dc
#     global inline_dc
#
#     input = file.read(1)
#     while input and not EOI:
#         if input == chr(0xFF):
#             cmd = file.read(1)
#             if cmd:
#                 # Byte stuffing
#                 if cmd == chr(0x00):
#                     input = chr(0xFF)
#                 # End of image marker
#                 elif cmd == chr(0xD9):
#                     EOI = True
#                 # Restart markers
#                 elif 0xD0 <= ord(cmd) <= 0xD7 and inline_dc:
#                     # Reset dc value
#                     dc = [0 for i in range(num_components + 1)]
#                     input = file.read(1)
#                 else:
#                     input = file.read(1)
#                     print
#                     "CMD: %x" % ord(cmd)
#
#         if not EOI:
#             for i in range(7, -1, -1):
#                 # Output next bit
#                 yield (ord(input) >> i) & 0x01
#
#             input = file.read(1)
#
#     while True:
#         yield []
#
#
# def get_bits(num, gen):
#     """ Get "num" bits from gen """
#     out = 0
#     for i in range(num):
#         out <<= 1
#         val = gen.next()
#         if val != []:
#             out += val & 0x01
#         else:
#             return []
#
#     return out
#
#
# def print_and_pause(fn):
#     def new(*args):
#         x = fn(*args)
#         print
#         x
#         raw_input()
#         return x
#
#     return new
#
#
# # @print_and_pause
# def read_data_unit(comp_num):
#     """ Read one DU with component id comp_num """
#     global bit_stream
#     global component
#     global dc
#
#     data = []
#
#     comp = component[comp_num]
#     huff_tbl = huffman_dc_tables[comp['Td']]
#
#     # Fill data with 64 coefficients
#     while len(data) < 64:
#         key = 0
#
#         for bits in range(1, 17):
#             key_len = []
#             key <<= 1
#             # Get one bit from bit_stream
#             val = get_bits(1, bit_stream)
#             if val == []:
#                 break
#             key |= val
#             # If huffman code exists
#             if huff_tbl.has_key((bits, key)):
#                 key_len = huff_tbl[(bits, key)]
#                 break
#
#         # After getting the DC value
#         # switch to the AC table
#         huff_tbl = huffman_ac_tables[comp['Ta']]
#
#         if key_len == []:
#             print(bits, key, bin(key)), "key not found"
#             break
#         # If ZRL fill with 16 zero coefficients
#         elif key_len == 0xF0:
#             for i in range(16):
#                 data.append(0)
#             continue
#
#         # If not DC coefficient
#         if len(data) != 0:
#             # If End of block
#             if key_len == 0x00:
#                 # Fill the rest of the DU with zeros
#                 while len(data) < 64:
#                     data.append(0)
#                 break
#
#             # The first part of the AC key_len
#             # is the number of leading zeros
#             for i in range(key_len >> 4):
#                 if len(data) < 64:
#                     data.append(0)
#             key_len &= 0x0F
#
#         if len(data) >= 64:
#             break
#
#         if key_len != 0:
#             # The rest of key_len is the amount
#             # of "additional" bits
#             val = get_bits(key_len, bit_stream)
#             if val == []:
#                 break
#             # Decode the additional bits
#             num = calc_add_bits(key_len, val)
#
#             # Experimental, doesn't work right
#             if len(data) == 0 and inline_dc:
#                 # The DC coefficient value
#                 # is added to the DC value from
#                 # the corresponding DU in the
#                 # previous MCU
#                 num += dc[comp_num]
#                 dc[comp_num] = num
#
#             data.append(num)
#         else:
#             data.append(0)
#
#     if len(data) != 64:
#         print
#         "Wrong size", len(data)
#
#     return data
#
#
# def restore_dc(data):
#     """ Restore the DC values as the DC values are coded as the difference from the previous DC value of the same component """
#     dc_prev = [0 for x in range(len(data[0]))]
#     out = []
#
#     # For each MCU
#     for mcu in data:
#         # For each component
#         for comp_num in range(len(mcu)):
#             # For each DU
#             for du in range(len(mcu[comp_num])):
#                 if mcu[comp_num][du]:
#                     mcu[comp_num][du][0] += dc_prev[comp_num]
#                     dc_prev[comp_num] = mcu[comp_num][du][0]
#
#         out.append(mcu)
#
#     return out
#
#
# def read_mcu():
#     """ Read an MCU """
#     global component
#     global num_components
#     global mcus_read
#
#     comp_num = mcu = range(num_components)
#
#     # For each component
#     for i in comp_num:
#         comp = component[i + 1]
#         mcu[i] = []
#         # For each DU
#         for j in range(comp['H'] * comp['V']):
#             if not EOI:
#                 mcu[i].append(read_data_unit(i + 1))
#
#     mcus_read += 1
#
#     return mcu
#
#
# def dequantify(mcu):
#     """ Dequantify MCU """
#     global component
#
#     out = mcu
#
#     # For each component
#     for c in range(len(out)):
#         # For each DU
#         for du in range(len(out[c])):
#             # For each coefficient
#             for i in range(len(out[c][du])):
#                 # Multiply by the the corresponding
#                 # value in the quantization table
#                 out[c][du][i] *= q_table[component[c + 1]['Tq']][i]
#
#     return out
#
#
# def zagzig(du):
#     """ Put the coefficients in the right order """
#     map = [[0, 1, 5, 6, 14, 15, 27, 28],
#            [2, 4, 7, 13, 16, 26, 29, 42],
#            [3, 8, 12, 17, 25, 30, 41, 43],
#            [9, 11, 18, 24, 31, 40, 44, 53],
#            [10, 19, 23, 32, 39, 45, 52, 54],
#            [20, 22, 33, 38, 46, 51, 55, 60],
#            [21, 34, 37, 47, 50, 56, 59, 61],
#            [35, 36, 48, 49, 57, 58, 62, 63]]
#
#     # Iterate over 8x8
#     for x in range(8):
#         for y in range(8):
#             if map[x][y] < len(du):
#                 map[x][y] = du[map[x][y]]
#             else:
#                 # If DU is too short
#                 # This shouldn't happen.
#                 map[x][y] = 0
#
#     return map
#
#
# def for_each_du_in_mcu(mcu, func):
#     """ Helper function that iterates over all DU's in an MCU and runs "func" on it """
#     return [map(func, comp) for comp in mcu]
#
#
# # @memoize
# def C(x):
#     if x == 0:
#         return 1.0 / sqrt(2.0)
#     else:
#         return 1.0
#
#
# # Lookup table to speed up IDCT somewhat
# idct_table = [[(C(u) * cos(((2.0 * x + 1.0) * u * pi) / 16.0)) for x in range(idct_precision)] for u in
#               range(idct_precision)]
# range8 = range(8)
# rangeIDCT = range(idct_precision)
#
#
# def idct(matrix):
#     """ Converts from frequency domain ordinary(?) """
#     out = [range(8) for i in range(8)]
#
#     # Iterate over every pixel in the block
#     for x in range8:
#         for y in range8:
#             sum = 0
#
#             # Iterate over every coefficient
#             # in the DU
#             for u in rangeIDCT:
#                 for v in rangeIDCT:
#                     sum += matrix[v][u] * idct_table[u][x] * idct_table[v][y]
#
#             out[y][x] = sum // 4
#
#     return out
#
#
# def expand(mcu, H, V):
#     """ Reverse subsampling """
#     Hout = max(H)
#     Vout = max(V)
#     out = [[[] for x in range(8 * Hout)] for y in range(8 * Vout)]
#
#     for i in range(len(mcu)):
#         Hs = Hout // H[i]
#         Vs = Vout // V[i]
#         Hin = H[i]
#         Vin = V[i]
#         comp = mcu[i]
#
#         if len(comp) != (Hin * Vin):
#             return []
#
#         for v in range(Vout):
#             for h in range(Hout):
#                 for y in range(8):
#                     for x in range(8):
#                         out[y + v * 8][x + h * 8].append(comp[(h // Hs) + Hin * (v // Vs)][y // Vs][x // Hs])
#
#     return out
#
#
# def combine_mcu(mcu):
#     global num_components
#
#     H = []
#     V = []
#
#     for i in range(num_components):
#         H.append(component[i + 1]['H'])
#         V.append(component[i + 1]['V'])
#
#     return expand(mcu, H, V)
#
#
# def combine_blocks(data):
#     global XYP
#
#     X, Y, P = XYP
#
#     out = [[(0, 0, 0) for x in range(X + 32)] for y in range(Y + 64)]
#     offsetx = 0
#     offsety = 0
#
#     for block in data:
#         ybmax = len(block)
#         for yb in range(ybmax):
#             xbmax = len(block[yb])
#             for xb in range(xbmax):
#                 out[yb + offsety][xb + offsetx] = tuple(block[yb][xb])
#         offsetx += xbmax
#         if offsetx > X:
#             offsetx = 0
#             offsety += ybmax
#
#     return out
#
#
# def crop_image(data):
#     global XYP
#     global Xdensity
#     global Ydensity
#
#     X, Y, P = XYP
#     return [[data[y][x] for x in range(X)] for y in range(Y)]
#
#
# def clip(x):
#     if x > 255:
#         return 255
#     elif x < 0:
#         return 0
#     else:
#         return int(x)
#
#
# def clamp(x):
#     x = (abs(x) + x) // 2
#     if x > 255:
#         return 255
#     else:
#         return x
#
# def YCbCr2RGB(Y, Cb, Cr):
#     Cred = 0.299
#     Cgreen = 0.587
#     Cblue = 0.114
#
#     R = Cr * (2 - 2 * Cred) + Y
#     B = Cb * (2 - 2 * Cblue) + Y
#     G = (Y - Cblue * B - Cred * R) / Cgreen
#
#     return clamp(R + 128), clamp(G + 128), clamp(B + 128)
#
#
# def YCbCr2Y(Y, Cb, Cr):
#     return Y, Y, Y
#
#
# def for_each_pixel(data, func):
#     out = [[0 for pixel in range(len(data[0]))] for line in range(len(data))]
#
#     for line in range(len(data)):
#         for pixel in range(len(data[0])):
#             out[line][pixel] = func(*data[line][pixel])
#
#     return out
#
#
# def tuplify(data):
#     out = []
#
#     for line in data:
#         out.append(tuple(line))
#
#     return tuple(out)
#
# def prepare(x, y, z):
#     return "#%02x%02x%02x" % (x, y, z)
#
#
# # def display_image(data):
# #     global XYP
# #
# #     X, Y, P = XYP
# #
# #     root = Tk()
# #     im = PhotoImage(width=X, height=Y)
# #
# #     im.put(data)
# #
# #     w = Label(root, image=im, bd=0)
# #     w.pack()
# #
# #     mainloop()

input_filename = 'warma.jpg'
jpeg_file = open(input_filename, "rb")

jpeg = JPEG()

in_char = jpeg_file.read(1)

while in_char:
    if ord(in_char) == 0xff:
        in_num = ord(jpeg_file.read(1))
        print("FF%02X" % in_num)
        if in_num == 0xd8:
            """读取到文件头"""
            print("SOI")
        elif 0xd0 <= in_num <= 0xd7:
            """RST标记，复位标记"""
            print("RST%x" % (in_num - 0xd0))
        elif 0xe0 <= in_num <= 0xef:
            """读取到图像识别信息"""
            print("APP%x" % (in_num - 0xe0))
            read_app(jpeg.APP0, in_num - 0xe0, jpeg_file)
        elif in_num == 0xdb:
            """读取到量化表"""
            print("DQT")
            read_dqt(jpeg.DQT, jpeg_file)
        elif in_num == 0xc0:
            """读取到图像基本信息"""
            print("SOF%x" % (in_num - 0xc0))
            read_sof(jpeg.SOF0, in_num - 0xc0, jpeg_file)
        elif in_num == 0xc4:
            """读取到huffman表"""
            print("DHT")
            read_dht(jpeg.DHT, jpeg_file)
        # elif in_num == 0xda:
        #     """读取到扫描行开始"""
        #     print("SOS")
        #     read_sos(jpeg_file)
        #     bit_stream = bit_read(jpeg_file)
        #     while not EOI:
        #         data.append(read_mcu())
        elif in_num == 0xd9:
            """读取到文件尾"""
            print("EOI")

    in_char = jpeg_file.read(1)

jpeg_file.close()



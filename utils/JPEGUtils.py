import heapq
from enum import Enum
from typing import Generator, Union
from utils.ReadUtils import *

import numpy as np
from math import sqrt, cos, pi


class JpegCommand(Enum):
    read_app0 = 1
    read_dqt = 2
    read_sof0 = 3
    read_dht = 4
    read_sos = 5
    read_stop = 6


def jpeg_bit_reader(file: BinaryIO) -> Generator[Union[int, JpegCommand], None, None]:
    signal = read_byte(file)
    while True:
        if signal == 0xff:
            cmd = read_byte(file)
            if cmd == 0x00:  # byte stuffing
                for i in range(7, -1, -1):
                    yield (signal >> i) & 0x01
            elif cmd == 0xc0:
                yield JpegCommand.read_sof0
            elif cmd == 0xc2:
                raise TypeError("Don't support SOF2 yet")
            elif cmd == 0xc4:
                yield JpegCommand.read_dht
            elif 0xd0 <= cmd <= 0xd7:  # reset signal, not support
                raise TypeError("Don't support reset yet: %x" % cmd)
            elif cmd == 0xd8:  # file head
                pass
            elif cmd == 0xd9:
                yield JpegCommand.read_stop
                break
            elif cmd == 0xda:
                yield JpegCommand.read_sos
            elif cmd == 0xdb:
                yield JpegCommand.read_dqt
            elif cmd == 0xdd:
                raise TypeError("Don't support DRI yet")
            elif 0xe0 <= cmd <= 0xef:
                if cmd == 0xe0:
                    yield JpegCommand.read_app0
                else:  # don't support other app types
                    raise TypeError("Don't support this app type yet: %s" % ("APP" + str(cmd - 0xe0)))
            elif cmd == 0xfe:
                raise TypeError("Don't support COM yet")
            else:
                raise TypeError("Unknown command: 0x%x" % cmd)
        else:
            for i in range(7, -1, -1):
                yield (signal >> i) & 0x01

        signal = read_byte(file)


def read_amplitude(size: int, data_stream: Generator[Union[int, JpegCommand], None, None]) -> int:
    amplitude = 0
    try:
        for i in range(size):
            amplitude <<= 1
            amplitude |= data_stream.__next__()
    except Exception:
        raise TypeError("Error in read_amplitude")
    # calculate the genuine value
    # for example: 001 -> -6, 101 -> 5
    if amplitude & (1 << (size - 1)):
        pass
    else:
        amplitude -= (1 << size) - 1
    return amplitude


def YCbCr2RGB(pixel: list[int, int, int]) -> list[int, int, int]:
    Y, Cb, Cr = pixel
    Cred = 0.299
    Cgreen = 0.587
    Cblue = 0.114

    R = Cr * (2 - 2 * Cred) + Y + 128
    B = Cb * (2 - 2 * Cblue) + Y + 128
    G = (Y - B * Cblue - R * Cred + 128) / Cgreen

    R = max(min(round(R), 255), 0)
    B = max(min(round(B), 255), 0)
    G = max(min(round(G), 255), 0)
    return [R, G, B]


def RGB2YCbCr(pixel: tuple[int, int, int]) -> list[int, int, int]:
    R, G, B = pixel[0], pixel[1], pixel[2]
    Cred = 0.299
    Cgreen = 0.587
    Cblue = 0.114
    Y = Cred * R + Cgreen * G + Cblue * B - 128
    Cb = (B - Y - 128) / (2 - 2 * Cblue)
    Cr = (R - Y - 128) / (2 - 2 * Cred)
    return [round(Y), round(Cb), round(Cr)]


def C(x):
    if x == 0:
        return 1.0 / sqrt(2.0)
    else:
        return 1.0


dct_table = np.array(
    [
        [
            [
                [
                    (
                            C(u) * C(v) / 4.0
                            * cos(((2.0 * i + 1.0) * u * pi) / 16.0)
                            * cos(((2.0 * j + 1.0) * v * pi) / 16.0)
                    ) for u in range(8)
                ] for v in range(8)
            ] for i in range(8)
        ] for j in range(8)
    ]
)

idct_table = np.array(
    [
        [
            [
                [
                    (
                            C(u) * C(v) / 4.0
                            * cos(((2.0 * i + 1.0) * u * pi) / 16.0)
                            * cos(((2.0 * j + 1.0) * v * pi) / 16.0)
                    ) for i in range(8)
                ] for j in range(8)
            ] for u in range(8)
        ] for v in range(8)
    ]
)


def DCT(data_unit: list[list[int]], dct_table: np.ndarray) -> list[list[int]]:
    dct = np.zeros([8, 8], dtype=float)
    for u in range(8):
        for v in range(8):
            dct += dct_table[u][v] * data_unit[u][v]
    return np.around(dct).tolist()


def IDCT(data_unit: list[list[int]], idct_table: np.ndarray) -> list[list[int]]:
    idct = np.zeros([8, 8], dtype=float)
    for u in range(8):
        for v in range(8):
            idct += idct_table[u][v] * data_unit[u][v]
    return np.around(idct).tolist()


def zigzag(mat: list[list[int]]) -> list[int]:
    res = []
    for k in range(15):
        for i in range(max(0, k - 7), min(8, k + 1)):
            j = k - i
            if k % 2 == 1:
                res.append(mat[i][j])
            else:
                res.append(mat[j][i])
    return res


def inv_zigzag(data_unit: list[int]) -> list[list[int]]:
    mat = [[0, 1, 5, 6, 14, 15, 27, 28],
           [2, 4, 7, 13, 16, 26, 29, 42],
           [3, 8, 12, 17, 25, 30, 41, 43],
           [9, 11, 18, 24, 31, 40, 44, 53],
           [10, 19, 23, 32, 39, 45, 52, 54],
           [20, 22, 33, 38, 46, 51, 55, 60],
           [21, 34, 37, 47, 50, 56, 59, 61],
           [35, 36, 48, 49, 57, 58, 62, 63]]
    for i in range(8):
        for j in range(8):
            mat[i][j] = data_unit[mat[i][j]]

    return mat


def quantization(data_unit: list[int], qtable: list[int]) -> None:
    for i in range(len(data_unit)):
        data_unit[i] = round(data_unit[i] / qtable[i])


def dequantization(data_unit: list[int], qtable: list[int]) -> None:
    for i in range(len(data_unit)):
        data_unit[i] *= qtable[i]


def recover_dc(mcu_list: list[list[list[list[int]]]]):
    for comp_id in range(3):
        pre_sum = 0
        for mcu in mcu_list:
            for data_unit in mcu[comp_id]:
                data_unit[0] += pre_sum
                pre_sum = data_unit[0]


def dpcm_on_dc(mcu_list: list[list[list[list[int]]]]):
    for comp_idx in range(3):
        pre = 0
        for mcu in mcu_list:
            for data_unit in mcu[comp_idx]:
                pre, data_unit[0] = data_unit[0], data_unit[0] - pre


# input: mcu_list
# output: list of huffman tables
# huffman tables: [symbol_cnt_for_each_len: list[int], symbols[int]]
def create_dc_huffman_tables(mcu_list: list[list[list[list[int]]]]) -> list[list[list[int], list[int]]]:
    # create 2 freq_dict, one for Y, and one for Cb, Cr
    freq_dict_list = [{}, {}]
    for mcu in mcu_list:
        for idx, comp in enumerate(mcu):
            if idx == 0:  # for Y layer
                freq_dict = freq_dict_list[0]
            else:  # for Cb and Cr
                freq_dict = freq_dict_list[1]
            for data_unit in comp:
                symbol = 0 if data_unit[0] == 0 else get_value_bit_len(data_unit[0])
                freq_dict[symbol] = freq_dict[symbol] + 1 if symbol in freq_dict else 1

    return create_huffman_tables_by_freq_dicts(freq_dict_list)


# input: mcu_list
# output: list of huffman tables
# huffman tables: [symbol_cnt_for_each_len: list[int], symbols[int]]
def create_ac_huffman_tables(mcu_list: list[list[list[list[int]]]]) -> list[list[list[int], list[int]]]:
    # create 2 freq_dict, one for Y, and one for Cb, Cr
    freq_dict_list = [{}, {}]
    for mcu in mcu_list:
        for idx, comp in enumerate(mcu):
            if idx == 0:  # for Y layer
                freq_dict = freq_dict_list[0]
            else:  # for Cb and Cr
                freq_dict = freq_dict_list[1]
            for data_unit in comp:
                idx = 1
                last_nonzero_idx = 64
                while last_nonzero_idx > 0 and data_unit[last_nonzero_idx-1] == 0:
                    last_nonzero_idx -= 1
                zero_cnt = 0
                while idx < last_nonzero_idx:
                    if data_unit[idx] == 0:
                        zero_cnt += 1
                        if zero_cnt == 16:  # special case
                            symbol = 0xf0
                            freq_dict[symbol] = freq_dict[symbol] + 1 if symbol in freq_dict else 1
                            zero_cnt = 0
                    else:
                        amplitude = data_unit[idx]
                        size = get_value_bit_len(amplitude)
                        symbol = zero_cnt << 4 | size
                        freq_dict[symbol] = freq_dict[symbol] + 1 if symbol in freq_dict else 1
                        zero_cnt = 0
                    idx += 1
                if last_nonzero_idx != 64:
                    symbol = 0
                    freq_dict[symbol] = freq_dict[symbol] + 1 if symbol in freq_dict else 1
    return create_huffman_tables_by_freq_dicts(freq_dict_list)


# input: freq_dict_list
# output: list of huffman tables
# huffman tables: [symbol_cnt_for_each_len: list[int], symbols[int]]
def create_huffman_tables_by_freq_dicts(freq_dict_list: list[dict]) -> list[list[list[int], list[int]]]:
    huffman_tables = []
    for freq_dict in freq_dict_list:
        h = []
        heapq.heapify(h)
        for symbol, freq in freq_dict.items():
            heapq.heappush(h, (freq, [(symbol, 0)]))  # tuple(freq, list[tuple(symbol, coding_length)])

        if len(h) == 1:  # if there is only one symbol to code, still need 1 bit
            h[0] = (h[0][0], [(h[0][1][0][0], h[0][1][0][1] + 1)])

        while len(h) > 1:
            t1 = heapq.heappop(h)
            t2 = heapq.heappop(h)
            symbol_list = []
            for sym_list in t1[1]:
                symbol_list.append((sym_list[0], sym_list[1] + 1))
            for sym_list in t2[1]:
                symbol_list.append((sym_list[0], sym_list[1] + 1))
            new_freq = t1[0] + t2[0]
            heapq.heappush(h, (new_freq, symbol_list))

        symbol_list = h[0][1]
        symbol_list = sorted(symbol_list, key=lambda x: x[1])
        symbols = []
        symbol_cnt_for_each_len = [0 for i in range(16)]
        for symbol, coding_len in symbol_list:
            symbols.append(symbol)
            symbol_cnt_for_each_len[coding_len-1] += 1
        huffman_tables.append([symbol_cnt_for_each_len, symbols])
    return huffman_tables


# complement code to represent value, return length
def get_value_bit_len(num: int) -> int:
    return len(get_complement_code(num))


def get_complement_code(num: int) -> str:
    flag = 1 if num > 0 else -1
    if num < 0:
        num = -num
    res = ''
    while num != 0:
        if flag == 1 and num & 0x01 == 0x01:
            res = '1' + res
        elif flag == -1 and num & 0x01 == 0x01:
            res = '0' + res
        elif flag == 1 and num & 0x01 == 0:
            res = '0' + res
        else:  # flag == -1 and num & 0x01 == 0
            res = '1' + res
        num >>= 1
    return res


def map_huff_symbol(huff_symbol_cnt_for_each_len: list[int], huff_symbol: list[int]) \
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


def map_symbol_to_coding(huff_symbol_cnt_for_each_len: list[int], huff_symbol: list[int]) -> dict[int, str]:
    cur_symbol_idx = 0
    table = {}
    cur_code = 0
    for i in range(len(huff_symbol_cnt_for_each_len)):
        cnt = huff_symbol_cnt_for_each_len[i]
        n_bits = i + 1
        for _ in range(cnt):
            code_str = str(bin(cur_code)).split('b')[1]
            huff_code = '0' * (n_bits - len(code_str)) + code_str
            table[huff_symbol[cur_symbol_idx]] = huff_code
            cur_code += 1
            cur_symbol_idx += 1
        cur_code <<= 1
    return table


if __name__ == "__main__":
    Y, Cb, Cr = [103.0, -14.0, 5.0]
    R, G, B = YCbCr2RGB([Y, Cb, Cr])
    print(R, G, B)
    print(RGB2YCbCr([R, G, B]))
    # import random
    # Y_max, Y_min, Cb_max, Cb_min, Cr_max, Cr_min = 0, 1000, 0, 1000, 0, 1000
    # for i in range(10000):
    #     r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    #     Y, Cb, Cr = RGB2YCbCr([r, g, b])
    #     Y_max = max(Y_max, Y)
    #     Y_min = min(Y_min, Y)
    #     Cb_max = max(Cb_max, Cb)
    #     Cb_min = min(Cb_min, Cb)
    #     Cr_max = max(Cr_max, Cr)
    #     Cr_min = min(Cr_min, Cr)
    #     print("r: %d, g:%d, b:%d; Y: %d, Cb: %d, Cr: %d" % (r, g, b, Y, Cb, Cr))
    # print(Y_max, Y_min, Cb_max, Cb_min, Cr_max, Cr_min)

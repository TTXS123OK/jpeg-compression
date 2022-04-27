from enum import Enum
from typing import Generator, Union
from utils.ReadUtils import *

import numpy as np
from math import sqrt, cos, pi, fabs


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
                    raise TypeError("Don't support this app type yet: %s" % ("APP" + str(cmd-0xe0)))
            elif cmd == 0xfe:
                raise TypeError("Don't support COM yet")
            else:
                raise TypeError("Unknown command")
        else:
            for i in range(7, -1, -1):
                yield (signal >> i) & 0x01

        signal = read_byte(file)


def read_amplitude(size: int, data_stream: Generator[Union[int, JpegCommand], None, None]) -> int:
    amplitude = 0
    for i in range(size):
        amplitude <<= 1
        amplitude |= data_stream.__next__()
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
    R = max(min(round(R), 255), 0)
    B = Cb * (2 - 2 * Cblue) + Y + 128
    B = max(min(round(B), 255), 0)
    # G = (Y - B * Cblue - R * Cred) / Cgreen
    G = Y - 0.3441363 * Cb - 0.71413636 * Cr + 128
    G = max(min(round(G), 255), 0)
    return [R, G, B]


def RGB2YCbCr(pixel: list[int, int, int]) -> list[int, int, int]:
    R, G, B = pixel
    Cred = 0.299
    Cgreen = 0.587
    Cblue = 0.114
    Y = Cred * R + Cgreen * G + Cblue * B
    Cb = (B - Y) / (2 - 2 * Cblue)
    Cr = (R - Y) / (2 - 2 * Cred)
    return [round(fabs(Y)), round(fabs(Cb)), round(fabs(Cr))]

# def YCbCr2RGB(pixel: list[int, int, int]) -> list[int, int, int]:
#     Y_ = (Y / 256) ** (1/2.2) * 256
#     R = 0.00456621 * (Y_ - 16) + 0 * (Cb - 128) + 0.00625893 * (Cr - 128)
#     G = 0.00456621 * (Y_ - 16) + -0.00153632 * (Cb - 128) + -0.00318811 * (Cr - 128)
#     B = 0.00456621 * (Y_ - 16) + 0 * (Cb - 128) + 0.00625893 * (Cr - 128)
#     return [round(R * 256), round(G * 256), round(B * 256)]
#
#
# def RGB2YCbCr(pixel: list[int, int, int]) -> list[int, int, int]:
#     R, G, B = pixel[0] / 256, pixel[1] / 256, pixel[2] / 256
#     R_, G_, B_ = R ** (1/2.2), G ** (1/2.2), B ** (1/2.2),
#     Y = 65.481 * R_ + 128.553 * G_ + 24.966 * B_ + 16
#     Cb = -37.797 * R_ + -74.203 * G_ + 112 * B_ + 128
#     Cr = 112 * R_ + -93.786 * G_ + -18.214 * B_ + 128
#     return [round(Y), round(Cb), round(Cr)]


def C(x):
    if x == 0:
        return 1.0 / sqrt(2.0)
    else:
        return 1.0

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


# data_unit: 2d int array, idct_table: 4d float array, return: 2d in array
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
        data_unit[i] *= qtable[i]


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


if __name__ == "__main__":
    Y, Cb, Cr = -37, -31, 104
    R, G, B = YCbCr2RGB([Y, Cb, Cr])
    print(R, G, B)
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
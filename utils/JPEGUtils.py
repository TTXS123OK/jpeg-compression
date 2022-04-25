from enum import Enum
from typing import Generator, Union
from ReadUtils import *


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


def YCbCr2RGB(pixel):
    Cred = 0.299
    Cgreen = 0.587
    Cblue = 0.114
    Y = pixel[0]
    Cb = pixel[1]
    Cr = pixel[2]
    R = max(min(int(Cr * (2 - 2 * Cred) + Y) + 128, 255), 0)
    B = max(min(int(Cb * (2 - 2 * Cblue) + Y) + 128, 255), 0)
    G = max(min(int(Y - 0.3441363 * Cb - 0.71413636 * Cr) + 128, 255), 0)
    return R, G, B
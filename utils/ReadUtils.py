from typing import BinaryIO


def read_byte(file: BinaryIO) -> int:
    """ Read a byte from file """
    return ord(file.read(1))


def read_word(file: BinaryIO) -> int:
    """ Read a 2 byte word from file """
    out = file.read(2)
    res = out[0] << 8 | out[1]
    return res

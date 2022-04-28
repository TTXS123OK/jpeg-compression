from typing import BinaryIO


def write_bytes(file: BinaryIO, byte_n: int, data: int) -> None:
    lst = []
    for i in range(byte_n):
        out = data & 0xff
        lst.append(out)
        data >>= 8

    for i in range(len(lst) - 1, -1, -1):
        out = lst[i]
        file.write(bytes([out]))


def write_str(file: BinaryIO, string: str):
    file.write(bytes(string, encoding='utf8'))


class BitWriter:

    def __init__(self, file: BinaryIO):
        self.file = file
        self.buf = 0
        self.buf_size = 0

    def write(self, binary_str: str):
        for bit in binary_str:
            if bit == '1':
                self.buf = (self.buf << 1) + 1  # don't forget this brace
            else:
                self.buf <<= 1
            self.buf_size += 1
            if self.buf_size == 8:
                self.file.write(bytes([self.buf]))
                self.buf = 0
                self.buf_size = 0

    def stop(self):
        self.file.write(bytes([self.buf]))
        self.buf = 0
        self.buf_size = 0

from io import RawIOBase
from typing import Tuple, List


def pack_str_len(s: bytes, head_len: int) -> bytes:
    return len(s).to_bytes(head_len, "little") + s


def unpack_str_len(s: bytes, head_len: int, pos: int) -> Tuple[bytes, int]:
    end = pos + head_len
    pos = end + int.from_bytes(s[pos: end], "little")
    return s[end: pos], pos


def unpack_str_len_fl(fl: RawIOBase, head_len: int) -> bytes:
    length = int.from_bytes(fl.read(head_len), "little")
    return fl.read(length)


def pack_str_len_fl(fl: RawIOBase, s: bytes, head_len: int):
    fl.write(len(s).to_bytes(head_len, "little"))
    fl.write(s)


def unpack_list_str_fl(fl: RawIOBase, head_len: int, str_head_len: int) -> List[bytes]:
    len_lst = int.from_bytes(fl.read(head_len), "little")
    return [
        fl.read(int.from_bytes(fl.read(str_head_len), "little"))
        for _ in range(len_lst)
    ]


def pack_list_str_fl(fl: RawIOBase, lst_str: List[bytes], head_len: int, str_head_len: int):
    fl.write(len(lst_str).to_bytes(head_len, "little"))
    for s in lst_str:
        fl.write(len(s).to_bytes(str_head_len, "little"))
        fl.write(s)
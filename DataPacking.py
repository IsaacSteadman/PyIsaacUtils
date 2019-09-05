from io import RawIOBase
from typing import Tuple, List, Union


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


class PackerFmt(object):

    def pack(self, data, fl: RawIOBase):
        raise NotImplementedError("Not Implemented")

    def unpack(self, fl: RawIOBase):
        raise NotImplementedError("Not Implemented")


class DataInt(PackerFmt):
    __slots__ = ["n_bytes", "num_off", "signed", "lsb_first"]

    def __init__(self, n_bytes: int=4, num_off: int=0, signed: bool=False, lsb_first: bool=True):
        self.n_bytes = n_bytes
        self.num_off = num_off
        self.signed = signed
        self.lsb_first = lsb_first

    def pack(self, data: int, fl: RawIOBase):
        byteorder = "little" if self.lsb_first else "big"
        byts = (data - self.num_off).to_bytes(self.n_bytes, byteorder, signed=self.signed)
        fl.write(byts)

    def unpack(self, fl: RawIOBase) -> int:
        byteorder = "little" if self.lsb_first else "big"
        return int.from_bytes(fl.read(self.n_bytes), byteorder, signed=self.signed)


class DataArray(PackerFmt):
    __slots__ = ["sub_dt", "head_len", "head_num_off", "hl_lsb_first"]

    def __init__(self, sub_dt: PackerFmt, head_len: int, head_num_off: int, hl_lsb_first: bool):
        # sub_dt means sub data type
        self.sub_dt = sub_dt
        self.head_len = head_len
        self.head_num_off = head_num_off
        self.hl_lsb_first = hl_lsb_first

    def pack(self, data: list, fl: RawIOBase):
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = len(data) - self.head_num_off
        assert ln >= 0
        fl.write(ln.to_bytes(self.head_len, byteorder, signed=False))
        for x in data:
            self.sub_dt.pack(x, fl)

    def unpack(self, fl: RawIOBase) -> list:
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = int.from_bytes(fl.read(self.head_len), byteorder, signed=False) + self.head_num_off
        rtn = [None] * ln
        for c in range(ln):
            rtn[c] = self.sub_dt.unpack(fl)
        return rtn


class DataVarBytes(PackerFmt):
    __slots__ = ["head_len", "head_num_off", "hl_lsb_first"]

    def __init__(self, head_len: int, head_num_off: int, hl_lsb_first: bool):
        self.head_len = head_len
        self.head_num_off = head_num_off
        self.hl_lsb_first = hl_lsb_first

    def pack(self, data: bytes, fl: RawIOBase):
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = len(data) - self.head_num_off
        assert ln >= 0
        fl.write(ln.to_bytes(self.head_len, byteorder, signed=False))
        fl.write(data)

    def unpack(self, fl: RawIOBase) -> bytes:
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = int.from_bytes(fl.read(self.head_len), byteorder, signed=False) + self.head_num_off
        return fl.read(ln)


class DataStruct(PackerFmt):
    __slots__ = ["lst_sub_dt"]

    def __init__(self, lst_sub_dt: List[PackerFmt]):
        self.lst_sub_dt = lst_sub_dt

    def pack(self, data: Union[list, tuple], fl: RawIOBase):
        lst_sub_dt = self.lst_sub_dt
        assert len(data) == len(lst_sub_dt)
        for c in range(len(lst_sub_dt)):
            lst_sub_dt[c].pack(data[c], fl)

    def unpack(self, fl: RawIOBase) -> list:
        lst_sub_dt = self.lst_sub_dt
        rtn = [None] * len(lst_sub_dt)
        for c in range(len(lst_sub_dt)):
            rtn[c] = lst_sub_dt[c].unpack(fl)
        return rtn


class DataKeyValue(PackerFmt):
    __slots__ = ["key_t", "val_t", "head_len", "head_num_off", "hl_lsb_first"]

    def __init__(self, key_t: PackerFmt, val_t: PackerFmt, head_len: int, head_num_off: int, hl_lsb_first: bool):
        self.key_t = key_t
        self.val_t = val_t
        self.head_len = head_len
        self.head_num_off = head_num_off
        self.hl_lsb_first = hl_lsb_first

    def pack(self, data: dict, fl: RawIOBase):
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = len(data) - self.head_num_off
        assert ln >= 0
        fl.write(ln.to_bytes(self.head_len, byteorder, signed=False))
        key_t = self.key_t
        val_t = self.val_t
        for key in data:
            key_t.pack(key, fl)
            val_t.pack(data[key], fl)

    def unpack(self, fl: RawIOBase) -> dict:
        byteorder = "little" if self.hl_lsb_first else "big"
        ln = int.from_bytes(fl.read(self.head_len), byteorder, signed=False) + self.head_num_off
        key_t = self.key_t
        val_t = self.val_t
        rtn = {}
        if isinstance(key_t, DataArray):
            for c in range(ln):
                key = tuple(key_t.unpack(fl))
                rtn[key] = val_t.unpack(fl)
        else:
            for c in range(ln):
                key = key_t.unpack(fl)
                rtn[key] = val_t.unpack(fl)
        return rtn

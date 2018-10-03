from typing import Union


def str_to_int(s: str, base: int = 10) -> Union[str, int]:
    assert 64 > base >= 1, "base must be less than 16 and greater than 1"
    if base <= 36:
        s = s.upper()
    n = 0
    for c, ch in enumerate(s):
        cv = ord(ch)
        v = 0
        if 0x41 <= cv <= 0x5a:
            v = cv - 55
        elif 0x61 <= cv <= 0x7a:
            v = cv - 61
        elif 0x30 <= cv <= 0x39:
            v = cv - 48
        elif ch == '_':
            v = 62
        elif ch == '$':
            v = 63
        elif ch == '-' and c == 0 and len(s) >= 2:
            n *= -1
            continue
        else:
            return "Non-digit character at c=%u, ch='%s'" % (c, ch)
        if v >= base:
            return "Invalid digit character for base %u at c=%u, ch='%s'" % (base, c, ch)
        n *= base
        n += v
    return n


StrToInt = str_to_int


if __name__ == "__main__":
    def assert_equal(x, y, msg=None):
        if msg is None:
            msg = "Expected %r to equal %r" % (x, y)
        else:
            msg = "Expected %r to equal %r" % (x, y) + msg
        assert x == y, msg
    import sys
    import traceback
    print("RUNNING TESTS")
    try:
        assert_equal(str_to_int("1"), 1)
        assert_equal(str_to_int("12"), 12)
        assert_equal(str_to_int("123"), 123)
        assert_equal(str_to_int("1234"), 1234)

        assert_equal(str_to_int("1", 16), 0x1)
        assert_equal(str_to_int("12", 16), 0x12)
        assert_equal(str_to_int("123", 16), 0x123)
        assert_equal(str_to_int("1234", 16), 0x1234)

        assert_equal(str_to_int("1", 36), 1)
        assert_equal(str_to_int("12", 36), 1 * 36 + 2)
        assert_equal(str_to_int("123", 36), 1 * 36 * 36 + 2 * 36 + 3)
        assert_equal(str_to_int("1234", 36), 1 * 36 * 36 * 36 + 2 * 36 * 36 + 3 * 36 + 4)
    except Exception as Exc:
        sys.stderr.write(traceback.format_exc())
    else:
        print("PASSED TESTS")

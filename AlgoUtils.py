def dummy_key_fn(lst, i):
    return lst[i]


def bisect_search_base(lst, val, key_fn=dummy_key_fn):
    end = len(lst)
    begin = 0
    while end - 2 > begin:
        pivot = (end + begin) >> 1
        v = key_fn(lst, pivot)
        if val > v: begin = pivot + 1
        else: end = pivot + 1
    while end - begin and key_fn(lst, begin) < val:
        begin += 1
    while end - begin and val < key_fn(lst, end - 1):
        end -= 1
    return begin, end
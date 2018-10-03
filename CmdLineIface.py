special_escape = {
    'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v'}
ext_escape = {'x': 2, 'u': 4, 'U': 8}


# Is Extended Escape character
# MaxLvl is in the maximum number of nybbles (4-bit groups)
def is_ext_esc_ch(ch, max_lvl):
    if ch.isdigit():
        return True
    if ch not in ext_escape:
        return False
    return ext_escape[ch] <= max_lvl


ch_escape = {'"', '\'', ' ', '\\'}


# MaxUniLvl is in the maximum number of nybbles (4-bit groups)
def parse_cmdline(cmdline, max_uni_lvl=2, max_tokens=None):
    global special_escape
    global ch_escape
    lst_tok = [""]
    quote = 0
    backslash = False
    c = 0
    for ch in cmdline:
        if quote > 0:
            lst_tok[-1] += ch
            if not backslash:
                if quote == 1 and ch == '\'' or quote == 2 and ch == '"':
                    quote = 0
                    if (max_tokens is not None) and len(lst_tok) >= max_tokens:
                        lst_tok[:] = lst_tok[:max_tokens] + [cmdline[c:]]
                        break
                    lst_tok.append("")
        elif ch == ' ':
            if backslash:
                lst_tok[-1] += ch
            elif len(lst_tok[-1]) > 0:
                if (max_tokens is not None) and len(lst_tok) >= max_tokens:
                    lst_tok[:] = lst_tok[:max_tokens] + [cmdline[c:]]
                    break
                lst_tok.append("")
        elif ch == '"':
            if backslash:
                lst_tok[-1] += ch
            else:
                quote = 2
                if len(lst_tok[-1]) > 0:
                    if (max_tokens is not None) and len(lst_tok) >= max_tokens:
                        lst_tok[:] = lst_tok[:max_tokens] + [cmdline[c:]]
                        break
                    lst_tok.append("")
                lst_tok[-1] += ch
        elif ch == '\'':
            if backslash:
                lst_tok[-1] += ch
            else:
                quote = 1
                if len(lst_tok[-1]) > 0:
                    if (max_tokens is not None) and len(lst_tok) >= max_tokens:
                        lst_tok[:] = lst_tok[:max_tokens] + [cmdline[c:]]
                        break
                    lst_tok.append("")
                lst_tok[-1] += ch
        else:
            lst_tok[-1] += ch
        if ch == '\\':
            backslash = not backslash
        else:
            backslash = False
        c += 1
    # print lst_tok
    add_return = None
    if max_tokens is not None and (len(lst_tok) - 1) == max_tokens:
        add_return = lst_tok.pop()
    lst_tok = list(filter(lambda x: len(x) > 0, lst_tok))
    for c in range(len(lst_tok)):
        if lst_tok[c][0] in ['"', '\'']:
            lst_tok[c] = lst_tok[c][1:-1]
        pos = -1
        new_str = ""
        while True:
            prev_pos = pos
            pos = lst_tok[c].find('\\', prev_pos + 1)
            if pos < 0:
                new_str += lst_tok[c][prev_pos + 1:]
                break
            new_str += lst_tok[c][prev_pos + 1:pos]
            pos += 1
            ch = lst_tok[c][pos]
            if ch in ch_escape:
                new_str += ch
            elif ch in special_escape:
                new_str += special_escape[ch]
            elif is_ext_esc_ch(ch, max_uni_lvl):
                if ch.isdigit():
                    i = 1
                    while i < 3:
                        if not lst_tok[c][pos + i].isdigit():
                            break
                        i += 1
                    # FIXME: was lst_tok[pos:pos + i]
                    new_str += chr(int(lst_tok[c][pos:pos + i], 8))
                    pos += i - 1
                else:
                    length = ext_escape[ch]
                    pos += 1
                    new_str += chr(int(lst_tok[c][pos:pos + length], 16))
                    pos += length - 1
            else:
                new_str += "\\" + ch
        lst_tok[c] = new_str
    if add_return is None:
        return lst_tok
    else:
        return lst_tok + [add_return]

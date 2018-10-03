import threading
import sys
import traceback
from CmdLineIface import parse_cmdline

try:
    import readline
except ImportError:
    try:
        import pyreadline as readline
    except ImportError:
        readline = None
        raise ImportError("Could not import pyreadline")


class BaseTerm(object):
    def out_ln_lk(self, *args): pass

    def out_ln(self, *args): pass

    def write(self, s): pass

    def write_lk(self, s): pass

    def write_err(self, s): self.write(s)

    def write_err_lk(self, s): self.write_lk(s)

    def read_line(self, prompt=""): return ""

    def read_pass(self, prompt=""): return self.read_line(prompt)

    def exit_term(self): pass


class CmdTerm(BaseTerm):
    def __init__(self):
        self.prompt = None
        self.lk = threading.Lock()

    def read_line(self, prompt=""):
        self.prompt = prompt
        rtn = input(self.prompt)
        self.prompt = None
        return rtn

    def write(self, s):
        self.pre_write(s)
        sys.stdout.write(s)
        self.post_write(s)

    def write_lk(self, s):
        with self.lk:
            self.write(s)

    def write_err(self, s):
        self.pre_write(s)
        sys.stderr.write(s)
        self.post_write(s)

    def write_err_lk(self, s):
        with self.lk:
            self.write_err(s)

    def out_ln(self, *args):
        self.write(" ".join(map(str, args)) + "\n")

    def out_ln_lk(self, *args):
        with self.lk:
            self.out_ln(*args)

    def pre_write(self, str_log):
        del str_log
        if self.prompt is not None:
            len_line = len(readline.get_line_buffer()) + len(self.prompt)
            sys.stdout.write("\r" + " " * len_line + "\r")

    def post_write(self, str_log):
        del str_log
        if self.prompt is not None:
            sys.stdout.write(self.prompt + readline.get_line_buffer())
            sys.stdout.flush()

    def logger_pre_w(self, log, c, str_log):
        if log.LstFl[c] == sys.stdout:
            self.pre_write(str_log)

    def logger_post_w(self, log, c, str_log):
        if log.LstFl[c] == sys.stdout:
            self.post_write(str_log)


class PrnTermGroup(BaseTerm):
    def __init__(self, lst_terms):
        self.Terms = set(lst_terms)
        self.lk = threading.Lock()

    def add_term(self, term_obj):
        with self.lk:
            self.Terms.add(term_obj)

    def remove_term(self, term_obj):
        with self.lk:
            self.Terms.discard(term_obj)

    def out_ln(self, *args):
        for Term in self.Terms:
            Term.out_ln(*args)

    def out_ln_lk(self, *args):
        with self.lk:
            for Term in self.Terms:
                Term.out_ln_lk(*args)

    def write(self, s):
        for Term in self.Terms:
            Term.write(s)

    def write_lk(self, s):
        with self.lk:
            for Term in self.Terms:
                Term.write_lk(s)

    def read_line(self, prompt=""):
        raise NotImplementedError("read_line is not useable on PrnTermGroup instances")


class PseudoStdout(object):
    def __init__(self, term_obj):
        assert isinstance(term_obj, BaseTerm)
        self.term_obj = term_obj
        self.LstWritten = []
        self.Buffer = ""

    def write(self, data):
        self.Buffer += data

    def flush(self):
        self.LstWritten.append(self.Buffer)
        self.term_obj.write_lk(self.Buffer)
        self.Buffer = ""

    def read(self, num=None):
        raise IOError("File not open for reading")

    def seek(self, offset, whence=0):
        pass

    def tell(self):
        return 0


class BaseCmdShell(object):
    pass


class ShellCmd(object):
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __call__(self, term_obj, shared_env, local_env, cmdline):
        term_obj.write("This command is using default __call__ (does nothing but print this)\n")


class ParsingShellCmd(ShellCmd):
    def __init__(self, name, func, max_uni_lvl=2):
        super(ParsingShellCmd, self).__init__(name, func)
        self.max_uni_lvl = max_uni_lvl

    def __call__(self, term_obj, shared_env, local_env, cmdline):
        self.func(term_obj, shared_env, local_env, parse_cmdline(cmdline, self.max_uni_lvl))


class PlainShellCmd(ShellCmd):
    def __call__(self, term_obj, shared_env, local_env, cmdline):
        self.func(term_obj, shared_env, local_env, cmdline)


class RtnNoEnvShellCmd(ShellCmd):
    def __call__(self, term_obj, shared_env, local_env, cmdline):
        term_obj.write(self.func(cmdline) + "\n")


class DictCmdShell(BaseCmdShell):
    # TODO: allow include command dictionary 'dct_cmds' in the class definition
    def __init__(self, dct_cmds, shared_dat, local_env, use_lower):
        assert isinstance(dct_cmds, dict)
        for k in dct_cmds:
            assert isinstance(k, str)
            if use_lower:
                assert k.islower()
            assert callable(dct_cmds[k])
        self.dct_cmds = dct_cmds
        self.env_dat = dict() if local_env is None else local_env
        self.shared_env = shared_dat
        self.use_lower = use_lower

    def dispatch(self, term_obj, cmd, cmdline):
        if self.use_lower:
            cmd = cmd.lower()
        if cmd not in self.dct_cmds:
            term_obj.write("Unrecognized Command '%s', type help for a list of commands" % cmd)
            return
        cmd = self.dct_cmds[cmd]
        # assert isinstance(Cmd, ShellCmd) and callable(Cmd)
        # noinspection PyBroadException
        try:
            cmd(term_obj, self.shared_env, self.env_dat, cmdline)
        except Exception as exc:
            del exc
            term_obj.write(traceback.format_exc())


def man_cmd(shell, args):
    if len(args) != 1:
        shell.term_obj.write("Must have a command name to show manual page for\n")
        return
    cmd = args[0].lower() if shell.use_lower else args[0]
    if cmd not in shell.dct_cmds:
        shell.term_obj.write("man could not find the command %s\n" % args[0])
        return
    func = shell.dct_cmds[cmd]
    if not hasattr(func, "man_page"):
        shell.term_obj.write(
            "The command %s does not provide a manual page\n" % args[0])
    else:
        shell.term_obj.write("man %s:\n%s\n" % (args[0], func.man_page))


class PythonRunner(object):
    def __init__(self, globs, locs, ps1, ps2):
        self.globs = globs
        self.locs = locs
        self.ps1 = ps1
        self.ps2 = ps2


def repl_shell(term_obj, globs, locs, ps1, ps2):
    use_locals = True
    while True:
        # noinspection PyBroadException
        try:
            inp = term_obj.read_line(ps1)
            inp1 = inp
            while inp1.startswith(" ") or inp1.startswith("\t") or inp1.endswith(":"):
                inp1 = term_obj.read_line(ps2)
                inp += "\n" + inp1
            if len(inp) == 0:
                continue
            elif inp.startswith("#"):
                lower = inp.lower()
                str0 = "#use-locals "
                str1 = "#exit-cur-repl"
                if lower.startswith(str0):
                    use_locals = int(inp[len(str0):])
                elif lower.startswith(str1):
                    break
            prn = None
            try:
                prn = eval(inp, globs, locs if use_locals else globs)
            except SyntaxError:
                exec(inp, globs, locs if use_locals else globs)
            if prn is not None:
                term_obj.write_lk(repr(prn))
        except Exception:
            term_obj.write_err_lk(traceback.format_exc())
        except (StopIteration, KeyboardInterrupt):
            term_obj.write_err_lk(traceback.format_exc())


def def_repl_runner(inp, globs, locs):
    """
    :param str|unicode inp:
    :param dict[str|unicode,any] globs:
    :param dict[str|unicode,any] locs:
    :rtype: (str|unicode, bool)
    """
    # noinspection PyBroadException
    try:
        prn = None
        try:
            prn = eval(inp, globs, locs)
        except SyntaxError:
            exec(inp, globs, locs)
        if prn is not None:
            return repr(prn) + "\n", False
    except (Exception, StopIteration, KeyboardInterrupt, GeneratorExit):
        return traceback.format_exc(), True
    return "", False


def repl_shell1(term_obj, globs, locs, ps1, ps2, fn=def_repl_runner, fn_is_stop=None):
    """

    :param fn_is_stop:
    :param BaseTerm term_obj:
    :param globs:
    :param locs:
    :param ps1:
    :param ps2:
    :param (str|unicode,dict[str|unicode,any],dict[str|unicode,any]) -> (str|unicode, bool) fn:
    """
    use_locals = True
    while True if fn_is_stop is None else not fn_is_stop():
        inp = term_obj.read_line(ps1)
        inp1 = inp
        while inp1.startswith(" ") or inp1.startswith("\t") or inp1.endswith(":"):
            inp1 = term_obj.read_line(ps2)
            inp += "\n" + inp1
        if len(inp) == 0:
            continue
        elif inp.startswith("#"):
            lower = inp.lower()
            str0 = "#use-locals "
            str1 = "#exit-cur-repl"
            if lower.startswith(str0):
                use_locals = int(inp[len(str0):])
                continue
            elif lower.startswith(str1):
                break
        prn, is_err = fn(inp, globs, locs if use_locals else globs)
        if is_err:
            term_obj.write_err_lk(prn)
        else:
            term_obj.write_lk(prn)


def yes_no_t(term_obj, caption):
    inp = term_obj.read_line(caption).lower()
    while inp not in {"yes", "no", "y", "n"}:
        term_obj.out_ln_lk("Please enter 'yes', 'no', 'y' or 'n'")
        inp = term_obj.read_line(caption).lower()
    return inp[0] == 'y'

"""A tiny, SAFE simulated shell over an in-memory filesystem.

Shared by every terminal challenge. No real shell, subprocess, or host filesystem
is ever involved: a command line is parsed and interpreted against a per-instance
dict. Nothing a player types can reach the server it runs on.

``run_ex`` returns standard output and standard error separately so the web
terminal can colour them differently. ``run`` is the older combined form.

Built-ins: pwd whoami id hostname uname echo ls cd cat head tail grep wc find
base64 strings file sudo help. Simple pipes (``cat x | grep y``) work.
Scenario-specific *programs* (a mock ``curl``, ``tshark``, a decoder script…)
are plain Python callables registered per scenario; see shell_scenarios.py.
"""
from __future__ import annotations

import base64 as b64
import binascii
import fnmatch
import posixpath
import shlex
from typing import Callable

# A program receives (shell, args, stdin, as_root) and returns (stdout, stderr).
Program = Callable[["FakeShell", list, str, bool], tuple]

MAX_OUTPUT = 64 * 1024
_INTERPRETERS = {"python", "python3", "bash", "sh"}
_PUNCTUATION = set("();<>|&")


class FakeShell:
    def __init__(self, files: dict, *, user: str = "ctf", home: str = "/home/ctf",
                 host: str = "lab", root_only: set | None = None,
                 sudo_nopasswd: list | None = None,
                 programs: dict[str, Program] | None = None):
        self.files = dict(files)                 # abspath -> content (str)
        self.user = user
        self.home = home
        self.host = host
        self.root_only = set(root_only or set())  # paths readable only as root
        self.sudo = list(sudo_nopasswd or [])     # binaries allowed via sudo
        # Bare names ("curl") are found like PATH tools; absolute paths
        # ("/home/x/decode.py") must be run as ./decode.py or python3 decode.py.
        self.programs = dict(programs or {})
        self.dirs = {"/", home}
        for p in self.files:
            parts = p.split("/")
            for i in range(1, len(parts)):
                self.dirs.add("/".join(parts[:i]) or "/")

    # -- path helpers ------------------------------------------------------
    def _resolve(self, cwd: str, path: str) -> str:
        if not path:
            path = "."
        if path == "~" or path.startswith("~/"):
            path = self.home + path[1:]
        if not path.startswith("/"):
            path = posixpath.join(cwd, path)
        return posixpath.normpath(path)

    def _children(self, d: str):
        d = d.rstrip("/") or "/"
        prefix = "" if d == "/" else d
        out = set()
        for p in list(self.files) + list(self.dirs):
            if p == d:
                continue
            if p.startswith(prefix + "/"):
                rest = p[len(prefix) + 1:]
                out.add(rest.split("/")[0])
        return sorted(out)

    @staticmethod
    def _root_dir(path: str) -> bool:
        return path == "/root" or path.startswith("/root/")

    def _read(self, cwd: str, arg: str, as_root: bool, tool: str):
        """Return (content, error) for a file argument."""
        p = self._resolve(cwd, arg)
        if p in self.root_only and not as_root:
            return None, f"{tool}: {arg}: Permission denied"
        if p in self.files:
            return self.files[p], None
        if p in self.dirs:
            return None, f"{tool}: {arg}: Is a directory"
        return None, f"{tool}: {arg}: No such file or directory"

    # -- public API --------------------------------------------------------
    def run(self, cwd: str, line: str) -> tuple[str, str]:
        """Legacy form: (combined output, new_cwd)."""
        r = self.run_ex(cwd, line)
        return "\n".join(x for x in (r["stdout"], r["stderr"]) if x), r["cwd"]

    def run_ex(self, cwd: str, line: str) -> dict:
        """Run one command line. Returns {"stdout", "stderr", "cwd"}."""
        line = (line or "").strip()
        if not line:
            return {"stdout": "", "stderr": "", "cwd": cwd}

        try:
            stages = self._split_pipeline(line)
        except ValueError:
            return {"stdout": "", "stderr": "syntax error: unterminated quote", "cwd": cwd}
        if stages is None:
            return {"stdout": "", "cwd": cwd,
                    "stderr": "This training shell supports single commands and "
                              "pipes (|) only: no ;  &&  >  <  or $( )."}

        stdin, errors = "", []
        for i, tokens in enumerate(stages):
            if not tokens:
                return {"stdout": "", "stderr": "syntax error near unexpected token `|'",
                        "cwd": cwd}
            out, err, new_cwd = self._command(cwd, tokens, stdin, piped=i > 0)
            if len(stages) == 1:
                cwd = new_cwd          # `cd` inside a pipeline changes nothing
            if err:
                errors.append(err)
            stdin = out
        return {"stdout": stdin[:MAX_OUTPUT], "stderr": "\n".join(errors)[:MAX_OUTPUT],
                "cwd": cwd}

    # -- parsing -----------------------------------------------------------
    @staticmethod
    def _split_pipeline(line: str):
        """Tokenise into pipeline stages. None = uses unsupported shell syntax."""
        lex = shlex.shlex(line, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        stages, current = [], []
        for tok in lex:
            if tok == "|":
                stages.append(current)
                current = []
            elif set(tok) <= _PUNCTUATION or "`" in tok:
                return None   # ; && || > < ( ) or backticks
            else:
                current.append(tok)
        stages.append(current)
        return stages

    # -- dispatch ----------------------------------------------------------
    def _command(self, cwd, tokens, stdin, piped=False, as_root=False):
        cmd, args = tokens[0], tokens[1:]

        if cmd == "sudo":
            if not args:
                return "", "usage: sudo <command>", cwd
            if args[0] == "-l":
                if self.sudo:
                    lines = "\n".join(f"    (root) NOPASSWD: {b}" for b in self.sudo)
                    return (f"User {self.user} may run the following commands on "
                            f"{self.host}:\n{lines}", "", cwd)
                return "", f"Sorry, user {self.user} may not run sudo on {self.host}.", cwd
            if args[0] in self.sudo or ("/usr/bin/" + args[0]) in self.sudo:
                out, err, _ = self._command(cwd, args, stdin, piped, as_root=True)
                return out, err, cwd
            return ("", f"Sorry, user {self.user} is not allowed to execute "
                        f"'{args[0]}' as root on {self.host}.", cwd)

        program, pargs = self._find_program(cwd, cmd, args)
        if program is not None:
            out, err = program(self, pargs, stdin, as_root)
            return out, err, cwd

        handler = getattr(self, "_cmd_" + cmd.replace("-", "_"), None)
        if handler is None or not cmd.replace("_", "").isalnum():
            if "/" in cmd:
                p = self._resolve(cwd, cmd)
                if p in self.files:
                    return "", f"bash: {cmd}: Permission denied", cwd
                return "", f"bash: {cmd}: No such file or directory", cwd
            return "", f"{cmd}: command not found", cwd
        return handler(cwd, args, stdin if piped else None, as_root)

    def _find_program(self, cwd, cmd, args):
        if cmd in _INTERPRETERS and args:
            target = self._resolve(cwd, args[0])
            if target in self.programs:
                return self.programs[target], args[1:]
            return None, args
        if "/" in cmd:
            return self.programs.get(self._resolve(cwd, cmd)), args
        return self.programs.get(cmd), args

    # -- built-ins: each returns (stdout, stderr, cwd) ---------------------
    def _cmd_pwd(self, cwd, args, stdin, as_root):
        return cwd, "", cwd

    def _cmd_whoami(self, cwd, args, stdin, as_root):
        return ("root" if as_root else self.user), "", cwd

    def _cmd_id(self, cwd, args, stdin, as_root):
        return (("uid=0(root) gid=0(root) groups=0(root)") if as_root else
                f"uid=1000({self.user}) gid=1000({self.user}) groups=1000({self.user})"), "", cwd

    def _cmd_hostname(self, cwd, args, stdin, as_root):
        return self.host, "", cwd

    def _cmd_uname(self, cwd, args, stdin, as_root):
        if any("a" in a for a in args if a.startswith("-")):
            return (f"Linux {self.host} 6.8.11-amd64 #1 SMP PREEMPT_DYNAMIC "
                    "x86_64 GNU/Linux"), "", cwd
        return "Linux", "", cwd

    def _cmd_echo(self, cwd, args, stdin, as_root):
        if args and args[0] == "-n":
            args = args[1:]
        return " ".join(args), "", cwd

    def _cmd_help(self, cwd, args, stdin, as_root):
        extra = sorted(posixpath.basename(p) for p in self.programs)
        text = ("Built-in commands:\n"
                "  pwd  ls [-la]  cd  cat  head  tail  grep  wc  find  file  strings\n"
                "  echo  base64 [-d]  whoami  id  hostname  uname  sudo [-l]\n"
                "  clear  history  help\n"
                "Pipes work:  cat notes.txt | grep password")
        if extra:
            text += "\nTools in this lab:  " + "  ".join(extra)
        return text, "", cwd

    def _cmd_cd(self, cwd, args, stdin, as_root):
        target = self._resolve(cwd, args[0] if args else self.home)
        if target in self.dirs:
            if self._root_dir(target) and not as_root:
                return "", f"bash: cd: {args[0]}: Permission denied", cwd
            return "", "", target
        if target in self.files:
            return "", f"bash: cd: {args[0]}: Not a directory", cwd
        return "", f"bash: cd: {args[0] if args else ''}: No such file or directory", cwd

    def _cmd_ls(self, cwd, args, stdin, as_root):
        flags = "".join(a[1:] for a in args if a.startswith("-"))
        paths = [a for a in args if not a.startswith("-")]
        target = self._resolve(cwd, paths[0]) if paths else cwd
        if target in self.files:
            names, base = [target.split("/")[-1]], posixpath.dirname(target)
        elif target in self.dirs:
            if self._root_dir(target) and not as_root:
                return "", f"ls: cannot open directory '{paths[0]}': Permission denied", cwd
            names, base = self._children(target), target
            if "a" not in flags:
                names = [n for n in names if not n.startswith(".")]
        else:
            return "", (f"ls: cannot access '{paths[0] if paths else target}': "
                        "No such file or directory"), cwd
        if "l" not in flags:
            if "a" in flags and target in self.dirs:
                names = [".", ".."] + names
            return "  ".join(names), "", cwd
        rows = []
        for n in names:
            full = posixpath.join(base, n)
            if full in self.dirs:
                rows.append(f"drwxr-xr-x 2 {self.user} {self.user}  4096 {n}")
            elif full in self.root_only:
                rows.append(f"-rw------- 1 root root {len(self.files[full]):5d} {n}")
            else:
                mode = "-rwxr-xr-x" if full in self.programs else "-rw-r--r--"
                rows.append(f"{mode} 1 {self.user} {self.user} {len(self.files[full]):5d} {n}")
        return "\n".join(rows), "", cwd

    def _file_or_stdin(self, cwd, files, stdin, as_root, tool):
        """Text for commands that read files or, in a pipe, standard input."""
        if not files:
            if stdin is None:
                return None, f"usage: {tool} <file>"
            return stdin, ""
        outs, errs = [], []
        for a in files:
            content, err = self._read(cwd, a, as_root, tool)
            (errs if err else outs).append(err or content)
        return "\n".join(outs), "\n".join(errs)

    def _cmd_cat(self, cwd, args, stdin, as_root):
        out, err = self._file_or_stdin(cwd, args, stdin, as_root, "cat")
        return out or "", err, cwd

    def _head_tail(self, cwd, args, stdin, as_root, tool):
        n, files, it = 10, [], iter(args)
        for a in it:
            if a == "-n":
                a = "-" + next(it, "")
            if a.startswith("-") and a[1:].isdigit():
                n = int(a[1:])
            elif a.startswith("-"):
                return "", f"{tool}: invalid option '{a}'", cwd
            else:
                files.append(a)
        out, err = self._file_or_stdin(cwd, files, stdin, as_root, tool)
        lines = (out or "").splitlines()
        lines = lines[:n] if tool == "head" else lines[len(lines) - n if n else len(lines):]
        return "\n".join(lines), err, cwd

    def _cmd_head(self, cwd, args, stdin, as_root):
        return self._head_tail(cwd, args, stdin, as_root, "head")

    def _cmd_tail(self, cwd, args, stdin, as_root):
        return self._head_tail(cwd, args, stdin, as_root, "tail")

    def _cmd_wc(self, cwd, args, stdin, as_root):
        files = [a for a in args if not a.startswith("-")]
        out, err = self._file_or_stdin(cwd, files, stdin, as_root, "wc")
        if out is None:
            return "", err, cwd
        lines, words, chars = len(out.splitlines()), len(out.split()), len(out)
        if "-l" in args:
            return str(lines), err, cwd
        return f"{lines} {words} {chars}", err, cwd

    def _cmd_grep(self, cwd, args, stdin, as_root):
        flags = "".join(a[1:] for a in args if a.startswith("-"))
        rest = [a for a in args if not a.startswith("-")]
        if not rest or (len(rest) < 2 and stdin is None):
            return "", "usage: grep [-i] [-v] <pattern> <file>", cwd
        pat = rest[0]
        out, err = self._file_or_stdin(cwd, rest[1:], stdin, as_root, "grep")
        fold = (lambda s: s.lower()) if "i" in flags else (lambda s: s)
        hits = [ln for ln in (out or "").splitlines()
                if (fold(pat) in fold(ln)) != ("v" in flags)]
        return "\n".join(hits), err, cwd

    def _cmd_find(self, cwd, args, stdin, as_root):
        base, rest, name = cwd, list(args), None
        if rest and not rest[0].startswith("-"):
            base, rest = self._resolve(cwd, rest[0]), rest[1:]
        if "-name" in rest:
            i = rest.index("-name")
            if i + 1 >= len(rest):
                return "", "find: missing argument to `-name'", cwd
            name = rest[i + 1]
        base = base.rstrip("/") or "/"
        if base not in self.dirs and base not in self.files:
            return "", f"find: '{args[0]}': No such file or directory", cwd
        results = [p for p in sorted(set(self.files) | self.dirs)
                   if (p == base or p.startswith(base + "/" if base != "/" else "/"))
                   and (name is None or fnmatch.fnmatch(p.split("/")[-1], name))]
        return "\n".join(results), "", cwd

    def _cmd_file(self, cwd, args, stdin, as_root):
        if not args:
            return "", "usage: file <file>", cwd
        p = self._resolve(cwd, args[0])
        if p in self.dirs:
            return f"{args[0]}: directory", "", cwd
        if p not in self.files:
            return "", f"{args[0]}: cannot open (No such file or directory)", cwd
        ext = p.rsplit(".", 1)[-1] if "." in posixpath.basename(p) else ""
        kind = {"pcap": "pcap capture file, microsecond ts (little-endian) - version 2.4",
                "py": "Python script, ASCII text executable",
                "sh": "Bourne-Again shell script, ASCII text executable",
                "bak": "ASCII text"}.get(ext, "ASCII text")
        return f"{args[0]}: {kind}", "", cwd

    def _cmd_strings(self, cwd, args, stdin, as_root):
        out, err = self._file_or_stdin(cwd, [a for a in args if not a.startswith("-")],
                                       stdin, as_root, "strings")
        keep = [ln for ln in (out or "").splitlines() if len(ln.strip()) >= 4]
        return "\n".join(keep), err, cwd

    def _cmd_base64(self, cwd, args, stdin, as_root):
        decode = any(a in ("-d", "--decode", "-D") for a in args)
        files = [a for a in args if not a.startswith("-")]
        out, err = self._file_or_stdin(cwd, files, stdin, as_root, "base64")
        if out is None:
            return "", err, cwd
        if not decode:
            return b64.b64encode(out.encode()).decode(), err, cwd
        try:
            raw = b64.b64decode("".join(out.split()), validate=True)
        except (binascii.Error, ValueError):
            return "", "base64: invalid input", cwd
        return printable(raw), err, cwd


def printable(raw: bytes) -> str:
    """Bytes as terminal text; unprintable bytes become '.' like a hex dump."""
    return "".join(chr(b) if 32 <= b < 127 or b in (9, 10) else "." for b in raw)

import argparse
import datetime
import os
import pathlib
import re
import subprocess
import textwrap
import time


if os.environ.get("BROWSER"):
    from playwright.sync_api import sync_playwright


class BaseRunner:
    def run(self, ex):
        for f in ex.seq:
            getattr(ex, f)(self)


class AdocExpect:
    def __init__(self):
        self.s = ""
        self.matches = {}

    def omit_rest(self):
        self.s += "...output omitted...\n"
        return self

    def omit_until(self, pattern):
        self.s += "...output omitted...\n"
        return self

    def expect_verbatim(self, line):
        self.s += line
        self.s += "\n"
        return self

    def expect_re(self, pattern, adoc, adoc_matches=None):
        self.s += adoc
        self.s += "\n"
        if adoc_matches:
            self.matches.update(adoc_matches)
        return self

class AdocRunner(BaseRunner):
    def adoc(self, adoc):
        print(textwrap.dedent(adoc)[1:], end="")

    def cmd_run(self, *cmd, expect=None, adoc_replace=None, check=None):
        full_cmd = ""
        for i, line in enumerate(cmd):
            leading_spaces = re.match(" +", line)
            if leading_spaces:
                full_cmd += leading_spaces[0]
                line = line.lstrip()

            full_cmd += "*"
            full_cmd += line

            # there are multiple lines and this is not the last line
            if len(cmd) > 1 and i != len(cmd) - 1:
                full_cmd += " \\"

            full_cmd += "*\n"
        full_cmd = full_cmd.rstrip()

        if adoc_replace:
            for src, dst in adoc_replace:
                full_cmd = full_cmd.replace(src, dst)

        expect_s = expect.s if expect else ""

        print(f"""[subs=+quotes]
----
[student@workstation ~]$ {full_cmd}
{expect_s}----""")

    def expect(self):
        return AdocExpect()

    def create_file(self, name, contents):
        contents = textwrap.dedent(contents).strip()
        print(f"""
[subs=+quotes]
----
[student@workstation ~]$ *vi {name}*
{contents}
----""")

    def wait(self, f, pause=1, retries=60):
        pass

    def is_adoc(self):
        return True

    def is_test(self):
        return False


class TestExpect:
    def __init__(self):
        self.expects = []
        self.matches = {}

    def omit_rest(self):
        def _omit_rest(out):
            return ""
        self.expects.append(_omit_rest)
        return self

    def omit_until(self, pattern):
        def _omit_until(out):
            print(f"Omitting until: {pattern}")
            match = re.search(pattern, out)
            assert match, f"Not found in {out}"
            return out[match.start():]
        self.expects.append(_omit_until)
        return self

    def expect_verbatim(self, verbatim_line):
        def _expect_verbatim(out):
            if not out.startswith(verbatim_line):
                print(f"Expecting: {verbatim_line}")
                print("      Got: " + out.split("\n")[0])
                assert False, "unexpected output"
            return out[len(verbatim_line) + 1:]
        self.expects.append(_expect_verbatim)
        return self

    def expect_re(self, pattern, adoc, adoc_matches=None):
        def _expect_re(out: str):
            line, rest = out.split("\n", maxsplit=1)

            print(f"Checking: {line}")
            print(f" pattern: {pattern}")
            print(f"    adoc: {adoc}")

            m = re.match(pattern, line)

            if not m:
                assert False, "didn't match"

            self.matches.update(m.groupdict())

            return rest
        self.expects.append(_expect_re)
        return self


    def run(self, cmd, check=True):
        r = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="UTF-8")
        print(f"output:\n{r.stdout}")
        if check:
            assert r.returncode == 0
        out = r.stdout
        for expect in self.expects:
            out = expect(out)
        assert not out

class TestRunner(BaseRunner):
    def __init__(self):
        self.debug_step = 0

    def adoc(self, adoc):
        pass

    def cmd_run(self, *cmd, expect=None, adoc_replace=None, check=True):
        full_cmd = " ".join(cmd)
        print(f"$ {full_cmd}")
        if expect:
            expect.run(full_cmd, check)
        else:
            subprocess.run(full_cmd, shell=True, check=check)

    def expect(self):
        return TestExpect()

    def create_file(self, name, contents):
        with open(name, "w") as f:
            f.write(textwrap.dedent(contents).lstrip())

    def wait(self, f, pause=1, retries=60):
        for i in range(0, retries):
            try:
                if f():
                    return
            except Exception as e:
                print(e)
            print(f"retry attempt {i}/{retries}, sleeping {pause}s")
            time.sleep(pause)
        assert False, "retries exceeded"

    def is_adoc(self):
        return False

    def is_test(self):
        return True

    def _run_steps(self, ex, steps):
        for i, f in enumerate(_py_steps(ex.seq)):
            if not steps or f in steps or str(i) in steps:
                print(f"executing {f} {datetime.datetime.now()}")
                print("*" * 80)
                try:
                    getattr(ex, f)(self)
                finally:
                    print(f"finished {f} {datetime.datetime.now()}")


    def run(self, ex, steps):
        os.chdir(os.environ["HOME"])
        if os.environ.get("BROWSER"):
            subprocess.run(["playwright", "install"], check=True)
            with sync_playwright() as self.playwright:
                self.new_browser()
                self._run_steps(ex, steps)
                self.browser.close()
        else:
            self._run_steps(ex, steps)

    def new_browser(self):
        self.browser = self.playwright.firefox.launch()
        self.context = self.browser.new_context(ignore_https_errors=True, viewport={"width": 900, "height": 600})
        self.page = self.context.new_page()

    def dbg_browser(self):
        path = f"/home/student/dbg-{self.debug_step:03}.png"
        self.page.screenshot(path=path)
        print(f"Screenshot saved to {path}")
        self.debug_step += 1


def cli_adoc(ex, args):
    AdocRunner().run(ex)


def cli_test(ex, args):
    steps = None
    if args.steps:
        steps = set(args.steps.split(","))
    TestRunner().run(ex, steps)


def cli_list_steps(ex, args):
    print("\n".join(map(str, enumerate(_py_steps(ex.seq)))))


def _py_steps(seq):
    return [s for s in seq if s.startswith("py_")]


def main(ex):
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers()
    adoc = sp.add_parser("adoc")
    adoc.set_defaults(func=cli_adoc)

    test = sp.add_parser("test")
    test.set_defaults(func=cli_test)
    test.add_argument("--steps", help="comma-separated list of step names or indices from list-steps to execute")

    test = sp.add_parser("list-steps")
    test.set_defaults(func=cli_list_steps)

    args = parser.parse_args()
    if "func" not in args:
        parser.error("no command supplied")

    args.func(ex=ex, args=args)

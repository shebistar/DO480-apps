import sys
import textwrap


class Tangle:
    def __init__(self):
        self.mode = "adoc"
        self.buf = []
        self.adoc_block_index = 0
        self.seq = []

    def start(self):
        print("""
class Exercise:
""")

    def finish_block(self):
        if self.mode == "adoc":

            adoc = textwrap.indent("".join(self.buf), prefix=" " * 12)

            print(f"""
    def adoc_{self.adoc_block_index}(self):
        self.adoc(\"\"\"
{adoc}        \"\"\")""")
            self.seq.append(f"adoc_{self.adoc_block_index}")

        if self.mode == "python":
            py = textwrap.indent("".join(self.buf), prefix=" " * 12)

            print(f"""
    def py_{self.exercise}(self):
{py}""")
            self.seq.append(f"py_{self.exercise}")

        self.buf = []

    def finish(self):
        print(f"""
    seq = {repr(self.seq)}

from do480 import weave
weave.main(Exercise)
""")


    def line(self, line):
        if self.mode == "adoc":
            if line.startswith("%test.py."):
                self.buf.pop()  # remove //// from adoc block
                self.finish_block()
                self.mode = "python"
                self.exercise = line.replace("%test.py.", "").strip()
                return
        if self.mode == "python":
            if line.startswith("////"):
                self.finish_block()
                self.mode = "adoc"
                self.adoc_block_index += 1
                return
        self.buf.append(line)


def main():
    tangle = Tangle()
    tangle.start()
    with open(sys.argv[1]) as f:
        for line in f.readlines():
            tangle.line(line)
    tangle.finish_block()
    tangle.finish()


if __name__ == "__main__":
    main()

"""门禁子检查的共享工具。

输出约定（与 tools/check.sh 一致）：
  PASS  ...
  FAIL  <file>:<line> ...   # 失败必须带文件与行号
  WARN  ...
  SKIP  ...
退出码：有 FAIL 即 1，否则 0。
"""

import os
import re
import sys

ROOT = os.environ.get("ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)


class Result:
    def __init__(self, name):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.warned = 0
        self.skipped = 0

    def ok(self, msg):
        self.passed += 1
        print("PASS  %s" % msg)

    def fail(self, msg):
        self.failed += 1
        print("FAIL  %s" % msg)

    def warn(self, msg):
        self.warned += 1
        print("WARN  %s" % msg)

    def skip(self, msg):
        self.skipped += 1
        print("SKIP  %s" % msg)

    def finish(self):
        print(
            "\ncheck %s: %d passed, %d failed, %d warnings, %d skipped"
            % (self.name, self.passed, self.failed, self.warned, self.skipped)
        )
        sys.exit(1 if self.failed else 0)


def rel(path):
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


def read_lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def walk_markdown(top, recursive=True):
    out = []
    if not os.path.isdir(top):
        return out
    if recursive:
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames.sort()
            for name in sorted(filenames):
                if name.endswith(".md"):
                    out.append(os.path.join(dirpath, name))
    else:
        for name in sorted(os.listdir(top)):
            path = os.path.join(top, name)
            if os.path.isfile(path) and name.endswith(".md"):
                out.append(path)
    return out


def has_section(lines, pattern):
    rx = re.compile(pattern)
    return any(rx.search(line) for line in lines if line.startswith("## "))

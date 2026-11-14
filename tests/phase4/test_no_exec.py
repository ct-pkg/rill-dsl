"""PH-4-E5：加载期不执行任何工具的结构断言。

用法：python3 tests/phase4/test_no_exec.py（退出 0 = 通过）。
只断言三件事，不启动 CLI：
1. ``rill.loader`` 可导入；
2. loader 源码不引用执行类 API（subprocess / socket / os.system / os.popen / shutil.which）；
3. ``check_program`` 只接受 AST 与 profile 名，没有 fakes / 宿主句柄入口。
"""

import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from rill import loader

FORBIDDEN = ("subprocess", "socket", "os.system", "os.popen", "shutil.which")


def main():
    path = inspect.getsourcefile(loader)
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    hits = [needle for needle in FORBIDDEN if needle in source]
    assert not hits, "loader.py 引用了执行类 API：%s" % hits

    params = list(inspect.signature(loader.check_program).parameters)
    assert params[:2] == ["program", "profile"], params
    assert "fakes" not in params, params

    print("PASS no-exec: loader 只消费 AST 与 profile 名，无执行类入口")


if __name__ == "__main__":
    main()

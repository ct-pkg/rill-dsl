# PH-7 红证

基线：`36a5b0c`（PH-7 任务清单复核与 E-2 归属修正之后）。
每节的红证都在对应实现提交之前采集，命令与输出原样保留；`exit` 是被测命令的退出码。

## T1 `[into]` 顺序与失败

- 命令：`python3 tests/phase7/test_into.py`
- 退出码：`1`
- 原始输出：

```text
Traceback (most recent call last):
  File "/Users/samxx/trae-ws/rill-dsl/tests/phase7/test_into.py", line 14, in <module>
    from rill.eval_simple import Interpreter
ModuleNotFoundError: No module named 'rill.eval_simple'
```

原因：`src/rill/eval_simple.py` 尚未存在，`[into]` 执行器没有落盘。

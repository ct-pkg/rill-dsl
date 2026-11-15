# CT 缺陷绕法登记：PH-46 `Map<K, 用户 struct>`（PH-15 首次建立）

> 本文件回答三件事：缺陷命中在哪、实测怎么绕、绕法要付什么代价。
> 复现根目录 `/tmp/ph15-map-probe`（不在仓库内），CT `v0.44.1`。只本地提交，不 push、不打 tag。

## 1. 命中点

PH-15 的四张表（map / fn / verb / profile）如果用 `Map<K, V>` 承载，会遇到 PH-46：
**元素按值存进容器的用户 struct，在 `ct build` 多单元模式下生成不可编译的共享头。**

```c
struct Point { int x; }
struct Box {
    Map<char *, Point> *values;   /* 命中的形态 */
}
```

原因不在业务代码，而在生成器：`MapEntry` 的 `value` 字段按值写进共享头，而共享头没有
包含元素定义所在的单元，元素在那里只有前向声明。`Vec<用户 struct>` 不受影响，因为它的
实例留在单元内。指标对比见 §2。

## 2. 实测命令与通过证据

探针最小到只有一个 `struct` 和一个 `Map` 字段；`CT_STD_DIR` 必须指向 ct-lang 的
`lib/std`，否则泛型声明会先被误解析（与 `ct-json-capability-blockers.md` §5.3 一致）。

```console
$ cd /tmp/ph15-map-probe
$ CT_STD_DIR=/Users/samxx/trae-ws/ct-lang/lib/std \
    ~/.local/bin/ct build src/bad.ct -o bad.out
'cc' -std=c99 -I '.ctbuild' '.ctbuild/Vec.c' ... '.ctbuild/bad.c' '-o' 'bad.out'
In file included from .ctbuild/Vec.c:3:
.ctbuild/Vec.h:30:18: error: field has incomplete type 'struct Point'
   30 |     struct Point value;
      |                  ^
.ctbuild/Str.h:16:8: note: forward declaration of 'struct Point'
   16 | struct Point;
      |        ^
1 error generated.
$ echo $?
1
```

两种绕法都能过，且生成的可执行文件可运行（`rc=0`）：

```console
$ CT_STD_DIR=/Users/samxx/trae-ws/ct-lang/lib/std \
    ~/.local/bin/ct build src/good_ptr.ct -o good_ptr.out
... 'cc' ... '-o' '/tmp/ph15-map-probe/good_ptr.out'
$ echo $?
0
$ ./good_ptr.out; echo $?
0

$ CT_STD_DIR=/Users/samxx/trae-ws/ct-lang/lib/std \
    ~/.local/bin/ct build src/good_void.ct -o good_void.out
$ echo $?
0
```

| 形态 | 单文件 `ctc` | `ct build` | 结论 |
| --- | --- | --- | --- |
| `Map<char *, Point>` | 通过 | **失败**（`incomplete type`，rc=1） | PH-46 命中 |
| `Map<char *, Point *>` | 通过 | **通过**（rc=0） | 绕法 1 |
| `Map<char *, void *>` | 通过 | **通过**（rc=0） | 绕法 2 |

## 3. 代价

| 绕法 | 写法变化 | 代价 |
| --- | --- | --- |
| 元素改成指针 | `Map<char *, Point *>`，`get` 返回 `Point **` | 每个值一次堆分配、一次指针跳转；释放要自己遍历；缓存局部性变差 |
| 元素擦成 `void *` | `Map<char *, void *>` + 强转 | 与上同，且丢类型检查（本来也没有） |
| 换有序表 | `Vec<struct Pair>` + 线性查找 | 查表 O(n)，表规模大时不可接受 |
| 不用容器 | 自建数组 + 线性查找 | 无泛型复用，但零生成器依赖；释放路径完全显式 |

## 4. PH-15 的实际取法

**本相没有使用 `Map`。** 四张表都在 `ct/rill_ct.ct` 的 `load_scan` 里用自建数组
（`LoadMap` / `LoadFn`）线性查找，键在插入时复制。这样：

- 不触发 PH-46，也不需要指针/`void *` 绕法；
- 与单文件 `ctc` 路线一致，不引入多单元头问题；
- 代价是查表 O(n) 与显式生命周期；对 0.1.0 的 fixture 规模（个位数表项）没有可测影响。

因此 E-5 的“绕法有实测命令、通过证据与代价”按**可选绕法**交付，而不是本相实现路径。
本相没有因此获得 `Map` 的只读表接口：多单元化的前置仍待立卡（见
`docs/reviews/closeout-14.md` §7），E-3 在 `docs/reviews/closeout-15.md` 里不计通过。

---

## 5. PH-51 指针接收者派发（PH-19 首次落到宿主接口）

### 5.1 命中点

宿主能力如果用 trait 的指针接收者方法，`.method()` 会被发射成 `S_f(&p)`（传 `S**`），
vtable 点静默错值。PH-19 的 `HostOps` 是五类能力的派发面，正好命中。

### 5.2 绕法与本相实测

`ct/src/host/host.h.ct` 用 C 函数指针表，第一参数显式传具体宿主：

```c
struct HostOps {
    void *ctx;
    HRes (*fs_read)(void *ctx, const char *path);
    HRes (*process_run)(void *ctx, const char *command, JVal *stdin_value);
    ...
};
```

调用点一律 `ops->fs_read(ops->ctx, path)`；`ShellHost` 只放数据，方法都是本单元
`static` 自由函数。

通过证据：

```console
$ test -z "$(grep -nE '\.get\(\)\.get\(' ct/src/host/*.ct)"; echo $?
0
$ python3 tools/diff/diff.py --layer host --profile shell
   fixtures=12 diffs=0 directed=5 directed_diffs=0
   RESULT: PASS
```

### 5.3 代价

- 手写派发约 130 行（参数校验 + 五个动词分支），没有方法链语法糖；
- 每个能力函数都要接收并强转 `void *ctx`，类型检查弱于 trait；
- 换来的是不命中 PH-51，且 `ct build` 下单元边界清晰。

## 6. `errno` 是宏，`ct` 前端不展开（PH-19）

### 6.1 命中点

```console
$ cat e.ct
#include <errno.h>
int main(void){ return errno; }
$ ct build e.ct --outdir gen -o e
e.ct:2:29: error: use of an undeclared variable
```

`errno` 在系统头里是宏（macOS 为 `(*__error())`），`ct` 前端把它当未声明变量。

### 6.2 绕法

在 `ct/src/host/shell.h.ct` 收一个访问器：

```c
static int sh_errno(void) { return (*__error()); }
```

所有错误分支改调 `sh_errno()`。`ct build` 与 `cc` 均通过（见 PH-19 的构建日志）。

### 6.3 代价

- 平台相关：`__error()` 是 macOS/BSD 的 errno 访问器；Linux 需要 `__errno_location()`；
- 0.1.0 的构建目标只有本机 macOS，因此先收在宿主单元里，等跨平台卡再抽。

## 7. `#define` 不跨单元（PH-19 再次命中）

### 7.1 命中点

`pub struct ShellHost { char profile[SH_PROFILE_MAX]; }` 在生成头里只有
`char profile[SH_PROFILE_MAX];`，没有 `#define`，`cc` 报：

```
error: use of undeclared identifier 'SH_PROFILE_MAX'
```

### 7.2 绕法

跨单元可见的 `pub struct` 字段用字面量长度（`char profile[128];`）；宏只留在本单元
的 `snprintf` 里用。与 PH-14 §3 的「宏不跨单元」是同一条限制。

### 7.3 代价

- 字面量 128 与宏 `SH_PROFILE_MAX` 两处维护；改名时要同时改；
- 不引入新的头文件机制，`ct build` 行为不变。

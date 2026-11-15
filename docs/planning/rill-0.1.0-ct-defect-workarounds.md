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

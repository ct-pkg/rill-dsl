"""RILL 0.1.x 加载期校验（PH-4）。

只消费 AST 与 profile 名：建 map/fn/verb 表、查名字、查同块重复短词；
不执行工具、不求值、不读宿主能力。规范依据：``docs/RILL-0.1.0.md``
§4.17、§4.18、§五、§4.20；错误码与规范缺口见 ``docs/phases/PH-4/card.md`` §8。

PH-4-T1 范围：``check`` 入口、MapTable 与同块重复短词；fn/verb 表在 T2/T3 补齐。
"""

from .errors import LoadError

PROFILES = ("shell", "agent")
PRINCIPAL_KINDS = {"shell": "os-user", "agent": "role"}

# §五.8 要求未知动词在加载期报错，但规范未定义 VerbRegistry 的载体；
# 这里固定 0.1.0 的动词集（§六 示例 + fakes/tools.json），见 PH-4 卡 §8 缺口 2。
DEFAULT_VERBS = (
    "read",
    "write",
    "parse",
    "send",
    "search",
    "replace",
    "contains",
    "review",
)


class LoadTables(object):
    """加载期建好的表；只读消费，不在本模块执行任何东西。"""

    def __init__(self, maps, functions, verbs, profile):
        self.maps = maps
        self.functions = functions
        self.verbs = verbs
        self.profile = profile


def load_profile(name):
    if name not in PROFILES:
        raise LoadError(
            "E-LOAD-PROFILE-UNKNOWN", "未知 profile %r" % name, 0, 0
        )
    return {"name": name, "kind": name, "principal": PRINCIPAL_KINDS[name]}


def check_program(program, profile="shell"):
    """对已解析的 AST 做加载期校验；返回只读表，不执行工具。"""
    host = load_profile(profile)
    maps = _collect_maps(program)
    return LoadTables(maps=maps, functions={}, verbs=set(DEFAULT_VERBS), profile=host)


def _collect_maps(program):
    """每个 ``//map{}`` 一张表；同块重复短词报错，跨块各自定义。"""
    tables = []
    for header in program.get("headers", []):
        if header["kind"] != "MapBlock":
            continue
        table = {}
        for entry in header["entries"]:
            short = entry["short"]
            if short in table:
                span = entry["span"]
                raise LoadError(
                    "E-LOAD-MAP-DUP-SHORT",
                    "短词 %r 在同一 //map{} 内重复定义" % short,
                    span["line"],
                    span["col"],
                )
            table[short] = (entry["marker"], entry["long"])
        tables.append(table)
    return tables

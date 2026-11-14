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

# PH-10：shell profile 额外有声明的宿主动词（进程与环境变量）。
# PH-11：agent profile 共用同一动词集；能力差异回到宿主实现，不写进语法。
# 缺口与裁定的取代关系见 PH-11 卡 §7 #6。
SHELL_VERBS = DEFAULT_VERBS + ("env", "run")
AGENT_VERBS = SHELL_VERBS


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
    functions = _collect_functions(program)
    _check_fn_defaults(functions)
    verbs = set(SHELL_VERBS if profile == "shell" else AGENT_VERBS)
    _check_nodes(program, functions, verbs)
    return LoadTables(maps=maps, functions=functions, verbs=verbs, profile=host)


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


def _collect_functions(program):
    """``FnDef.name`` 精确匹配；同块重名不报错，登记为缺口（PH-4 卡 §8 #5）。"""
    functions = {}
    for header in program.get("headers", []):
        if header["kind"] != "FnBlock":
            continue
        for definition in header["defs"]:
            functions.setdefault(definition["name"], definition)
    return functions


def template_params(definition):
    """§4.18：模板 ``$变量`` 去重后按首次出现顺序；返回 ``(names, defaults)``。"""
    names = []
    defaults = {}
    for stage in definition["template"]:
        _collect_params(stage, names, defaults)
    return names, defaults


def _collect_params(node, names, defaults):
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    if kind == "Variable":
        if node["name"] not in names:
            names.append(node["name"])
        return
    if kind == "Default":
        if node["name"] not in names:
            names.append(node["name"])
        defaults.setdefault(node["name"], node["value"])
        return
    if kind == "VerbCall":
        _collect_params(node["subject"], names, defaults)
        _collect_params(node["object"], names, defaults)
        for item in node["post"]:
            _collect_params(item, names, defaults)
        return
    if kind == "Adverb":
        for item in node["items"]:
            _collect_params(item, names, defaults)
        return
    if kind == "PrepPhrase":
        _collect_params(node["object"], names, defaults)


def _check_fn_defaults(functions):
    """§4.18：默认值只允许尾部连续省略，中间缺省在加载期报错。"""
    for definition in functions.values():
        names, defaults = template_params(definition)
        tail_started = False
        for name in names:
            if name in defaults:
                tail_started = True
            elif tail_started:
                span = definition["span"]
                raise LoadError(
                    "E-LOAD-FN-DEFAULT-NOT-TAIL",
                    "函数 %r 的默认值只能出现在尾部；$%s 缺少默认值"
                    % (definition["name"], name),
                    span["line"],
                    span["col"],
                )


def _check_arity(call, definition):
    """§4.18：实参按位置绑定，数量不匹配直接报错，不补默认值。"""
    names, defaults = template_params(definition)
    given = len(call["args"])
    missing = [
        name for name in names[given:] if name not in defaults
    ] if given < len(names) else []
    if given > len(names) or missing:
        span = call["span"]
        raise LoadError(
            "E-LOAD-FN-ARITY",
            "函数 %r 需要 %d 个实参，实际 %d 个"
            % (definition["name"], len(names), given),
            span["line"],
            span["col"],
        )


def _check_nodes(node, functions, verbs):
    """查 ``@ STRING`` 的名字与 ``VerbCall`` 的动词；不解绑实参。"""
    if isinstance(node, list):
        for item in node:
            _check_nodes(item, functions, verbs)
        return
    if not isinstance(node, dict) or "kind" not in node:
        return
    if node["kind"] == "CallStmt":
        span = node["span"]
        definition = functions.get(node["name"])
        if definition is None:
            raise LoadError(
                "E-LOAD-FN-UNDECLARED",
                "未声明的函数 %r；只能调用 //fn{} 内定义的名字" % node["name"],
                span["line"],
                span["col"],
            )
        _check_arity(node, definition)
    if node["kind"] == "VerbCall" and node["verb"] not in verbs:
        span = node["span"]
        raise LoadError(
            "E-LOAD-VERB-UNKNOWN",
            "未知动词 %r；0.1.0 动词集见 PH-4 卡 §8" % node["verb"],
            span["line"],
            span["col"],
        )
    for key, value in node.items():
        if key in ("kind", "span"):
            continue
        _check_nodes(value, functions, verbs)

"""RILL 0.1.x 加载期校验（PH-4 / PH-22）。

只消费 AST 与 profile 名：建 map 表、函数形状表、verb 表，查同块重复短词与
函数形状冲突；不执行工具、不求值、不读宿主能力。规范依据：
``docs/RILL-0.1.0.md`` §4.17、§4.18、§4.20、§五；函数形状规则见
``docs/decisions/D-022.md`` 与 ``docs/phases/PH-22/card.md``。

函数没有名字：签名是模板第一段机械导出的形状键（``shape.py``）。同一
``//fn{}`` 内同形报 ``E-03``；调用无候选报 ``E-04``；多候选报 ``E-05``。
"""

from . import shape
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
    """按文档顺序收集全部 ``FnDef``；同一 ``//fn{}`` 内同形报 ``E-03``。"""
    functions = []
    for header in program.get("headers", []):
        if header["kind"] != "FnBlock":
            continue
        seen = []
        for definition in header["defs"]:
            for first in seen:
                if first["shape"] == definition["shape"]:
                    span = definition["span"]
                    first_span = first["span"]
                    raise LoadError(
                        "E-03",
                        "函数形状重复：%s" % shape.describe(definition["shape"]),
                        span["line"],
                        span["col"],
                        hint="首个同形定义在第 %d 行；两份形状均为 %s"
                        % (first_span["line"], shape.describe(definition["shape"])),
                    )
            seen.append(definition)
            functions.append(definition)
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
    for definition in functions:
        names, defaults = template_params(definition)
        tail_started = False
        for name in names:
            if name in defaults:
                tail_started = True
            elif tail_started:
                span = definition["span"]
                raise LoadError(
                    "E-LOAD-FN-DEFAULT-NOT-TAIL",
                    "函数形状 %s 的默认值只能出现在尾部；$%s 缺少默认值"
                    % (shape.describe(definition["shape"]), name),
                    span["line"],
                    span["col"],
                )


def _position_count(call):
    count = 1  # 宾语位始终存在
    if call["subject"] is not None:
        count += 1
    count += sum(1 for item in call["post"] if item["kind"] == "PrepPhrase")
    return count


def _check_call(node, functions):
    span = node["span"]
    call = node["call"]
    call_shape = shape.shape_of(call, template=False)
    exact, arity = shape.find(functions, call_shape)
    if exact:
        if len(exact) > 1:
            lines = ", ".join(str(item["span"]["line"]) for item in exact)
            raise LoadError(
                "E-05",
                "函数形状二义：%s" % shape.describe(call_shape),
                span["line"],
                span["col"],
                hint="候选定义行：%s" % lines,
            )
        return
    if arity:
        definition = arity
        raise LoadError(
            "E-LOAD-FN-ARITY",
            "函数形状 %s 需要 %d 个位置，实际 %d 个"
            % (
                shape.describe(definition["shape"]),
                _position_count(definition["template"][0]),
                _position_count(call),
            ),
            span["line"],
            span["col"],
        )
    same_verb = [
        shape.describe(item["shape"])
        for item in functions
        if item["shape"]["verb"] == call_shape["verb"]
    ]
    hint = (
        "同动词已定义形状：%s" % "；".join(same_verb)
        if same_verb
        else "同动词没有已定义形状"
    )
    raise LoadError(
        "E-04",
        "未声明的函数形状：%s" % shape.describe(call_shape),
        span["line"],
        span["col"],
        hint=hint,
    )


def _check_nodes(node, functions, verbs):
    """按文档顺序查 ``CallStmt`` 的形状与 ``VerbCall`` 的动词。"""
    if isinstance(node, list):
        for item in node:
            _check_nodes(item, functions, verbs)
        return
    if not isinstance(node, dict) or "kind" not in node:
        return
    if node["kind"] == "CallStmt":
        _check_call(node, functions)
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

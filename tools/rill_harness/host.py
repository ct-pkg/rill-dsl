"""HostProfile / HostCapabilities 骨架。

只定形状与加载入口，不落能力语义：
  - 五个槽位固定为 process / fs / env / stdio / exit；
  - 每个槽位只声明 provider 与 ref，ref 的内容本模块不解释；
  - 绑定对象由调用方通过 resolver 提供，本模块只负责放进对应槽位。

因此 Shell 与 Agent 的差异只允许出现在 profile 文件与绑定对象里，不允许回到语法或 AST。
"""

import json
import os

SCHEMA = "rill.host-profile/0"
CAPABILITY_SLOTS = ("process", "fs", "env", "stdio", "exit")
HOST_KINDS = ("shell", "agent")
PROFILE_KEYS = ("schema", "name", "kind", "description", "capabilities")
BINDING_KEYS = ("provider", "ref")


class ProfileError(ValueError):
    pass


class CapabilityBinding(object):
    def __init__(self, slot, provider, ref):
        self.slot = slot
        self.provider = provider
        self.ref = ref

    def __repr__(self):
        return "CapabilityBinding(%s, %s, %s)" % (self.slot, self.provider, self.ref)


class HostProfile(object):
    """一个宿主的声明式外壳；不含任何能力语义。"""

    def __init__(self, name, kind, capabilities, path, description=""):
        self.name = name
        self.kind = kind
        self.capabilities = capabilities
        self.path = path
        self.description = description

    def __repr__(self):
        return "HostProfile(%s, %s)" % (self.name, self.kind)


class HostCapabilities(object):
    """运行时拿到的五个能力句柄；本模块不定义它们怎么工作。"""

    def __init__(self, profile, process, fs, env, stdio, exit):
        self.profile = profile
        self.process = process
        self.fs = fs
        self.env = env
        self.stdio = stdio
        self.exit = exit

    def slot(self, name):
        if name not in CAPABILITY_SLOTS:
            raise KeyError("未知能力槽位 %r" % name)
        return getattr(self, name)


def load_profile(path):
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ProfileError("%s: 无法读取（%s）" % (path, exc))

    if not isinstance(doc, dict):
        raise ProfileError("%s: 顶层必须是对象" % path)
    for key in sorted(doc):
        if key not in PROFILE_KEYS:
            raise ProfileError("%s: 未知字段 %r" % (path, key))
    if doc.get("schema") != SCHEMA:
        raise ProfileError("%s.schema: 必须是 %s" % (path, SCHEMA))
    if not isinstance(doc.get("name"), str) or not doc["name"]:
        raise ProfileError("%s.name: 必须是非空字符串" % path)
    expected_name = os.path.splitext(os.path.basename(path))[0]
    if doc["name"] != expected_name:
        raise ProfileError("%s.name: 必须与文件名一致（%s）" % (path, expected_name))
    if doc.get("kind") not in HOST_KINDS:
        raise ProfileError("%s.kind: 必须是 %s" % (path, " / ".join(HOST_KINDS)))

    caps = doc.get("capabilities")
    if not isinstance(caps, dict):
        raise ProfileError("%s.capabilities: 必须是对象" % path)
    missing = [slot for slot in CAPABILITY_SLOTS if slot not in caps]
    extra = [slot for slot in caps if slot not in CAPABILITY_SLOTS]
    if missing:
        raise ProfileError("%s.capabilities: 缺少槽位 %s" % (path, ", ".join(missing)))
    if extra:
        raise ProfileError("%s.capabilities: 未知槽位 %s" % (path, ", ".join(extra)))

    bindings = {}
    for slot in CAPABILITY_SLOTS:
        item = caps[slot]
        if not isinstance(item, dict):
            raise ProfileError("%s.capabilities.%s: 必须是对象" % (path, slot))
        for key in sorted(item):
            if key not in BINDING_KEYS:
                raise ProfileError("%s.capabilities.%s: 未知字段 %r" % (path, slot, key))
        provider = item.get("provider")
        ref = item.get("ref")
        if not isinstance(provider, str) or not provider:
            raise ProfileError("%s.capabilities.%s.provider: 必须是非空字符串" % (path, slot))
        if not isinstance(ref, str) or not ref:
            raise ProfileError("%s.capabilities.%s.ref: 必须是非空字符串" % (path, slot))
        bindings[slot] = CapabilityBinding(slot, provider, ref)

    return HostProfile(
        doc["name"],
        doc["kind"],
        bindings,
        path,
        doc.get("description", ""),
    )


def load_profiles(root):
    """加载 testdata/0.1.0/profiles/*.json，按 name 排序。"""
    directory = os.path.join(root, "profiles")
    profiles = {}
    if not os.path.isdir(directory):
        return profiles
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        profile = load_profile(os.path.join(directory, name))
        if profile.name in profiles:
            raise ProfileError("%s: profile 名重复 %r" % (directory, profile.name))
        profiles[profile.name] = profile
    return profiles


def bind_capabilities(profile, resolver):
    """把 profile 声明的 ref 交给 resolver，得到五个句柄。

    resolver 的签名是 resolver(binding) -> object。它决定 provider/ref 怎么变成能力对象；
    本模块只保证五个槽位一个不少、名字不改。
    """
    handles = {}
    for slot in CAPABILITY_SLOTS:
        handles[slot] = resolver(profile.capabilities[slot])
    return HostCapabilities(profile, **handles)

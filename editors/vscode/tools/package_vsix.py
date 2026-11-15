#!/usr/bin/env python3
"""把 VS Code 插件目录打成可离线安装的 .vsix。

不依赖 node/npm/vsce：.vsix 本质是带 vsixmanifest 的 zip。
用法：
    python3 tools/package_vsix.py                 # 生成 dist/rill-dsl-<version>.vsix
    python3 tools/package_vsix.py --check <path>  # 校验已生成的 vsix
"""

import argparse
import json
import os
import sys
import zipfile
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
  <Default Extension=".txt" ContentType="text/plain"/>
</Types>
"""


def load_manifest():
    with open(os.path.join(ROOT, "package.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_files(manifest):
    files = [
        "package.json",
        "extension.js",
        "language-configuration.json",
        "README.md",
        "DESIGN.md",
        "syntaxes/rill.tmLanguage.json",
    ]
    lib_dir = os.path.join(ROOT, "lib")
    if os.path.isdir(lib_dir):
        for name in sorted(os.listdir(lib_dir)):
            if name.endswith(".js"):
                files.append("lib/" + name)
    missing = [name for name in files if not os.path.isfile(os.path.join(ROOT, name))]
    if missing:
        raise SystemExit("缺少打包文件：%s" % ", ".join(missing))
    for contribution in manifest["contributes"]["languages"]:
        path = contribution.get("configuration")
        if path and path.lstrip("./") not in files:
            files.append(path.lstrip("./"))
    for grammar in manifest["contributes"]["grammars"]:
        path = grammar.get("path")
        if path and path.lstrip("./") not in files:
            files.append(path.lstrip("./"))
    return files


def vsix_manifest(manifest):
    publisher = manifest["publisher"]
    name = manifest["name"]
    version = manifest["version"]
    display = escape(manifest.get("displayName", name))
    description = escape(manifest.get("description", ""))
    categories = "".join(
        "<Category>%s</Category>" % escape(item)
        for item in manifest.get("categories", [])
    )
    tags = ",".join(manifest.get("keywords", []))
    engine = manifest.get("engines", {}).get("vscode", "*")
    return """<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011" xmlns:d="http://schemas.microsoft.com/developer/vsx-schema-design/2011">
  <Metadata>
    <Identity Language="en-US" Id="{name}" Version="{version}" Publisher="{publisher}" />
    <DisplayName>{display}</DisplayName>
    <Description xml:space="preserve">{description}</Description>
    <Categories>{categories}</Categories>
    <Tags>{tags}</Tags>
    <GalleryFlags>Public</GalleryFlags>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{engine}" />
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace" />
    </Properties>
  </Metadata>
  <Installation>
    <InstallationTarget Id="Microsoft.VisualStudio.Code" />
  </Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Code.Readme" Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>
""".format(
        name=name,
        version=version,
        publisher=publisher,
        display=display,
        description=description,
        categories=categories,
        tags=escape(tags),
        engine=escape(engine),
    )


def write_entry(archive, name, data):
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build(output):
    manifest = load_manifest()
    files = collect_files(manifest)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        write_entry(archive, "[Content_Types].xml", CONTENT_TYPES)
        write_entry(archive, "extension.vsixmanifest", vsix_manifest(manifest))
        for relative in files:
            path = os.path.join(ROOT, relative)
            with open(path, "rb") as handle:
                write_entry(archive, "extension/" + relative, handle.read())
    return output


def check(path):
    manifest = load_manifest()
    required = {"[Content_Types].xml", "extension.vsixmanifest"}
    problems = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for name in sorted(required):
            if name not in names:
                problems.append("缺少 %s" % name)
        for name in names:
            if not (name == "extension.vsixmanifest" or name.startswith("extension/")):
                if name != "[Content_Types].xml":
                    problems.append("非预期根条目 %s" % name)
            if any(part in name for part in ("/test/", "/tools/", "/dist/", "__pycache__")):
                problems.append("不应打包的条目 %s" % name)
            if name.endswith(".DS_Store"):
                problems.append("不应打包的条目 %s" % name)
        if "extension.vsixmanifest" in names:
            text = archive.read("extension.vsixmanifest").decode("utf-8")
            expected = 'Id="%s" Version="%s" Publisher="%s"' % (
                manifest["name"],
                manifest["version"],
                manifest["publisher"],
            )
            if expected not in text:
                problems.append("manifest Identity 与 package.json 不一致：期望 %s" % expected)
        for relative in collect_files(manifest):
            if "extension/" + relative not in names:
                problems.append("缺少插件文件 extension/%s" % relative)
        size = sum(info.file_size for info in archive.infolist())
    if problems:
        print("VSIX 校验失败：")
        for problem in problems:
            print("  - " + problem)
        return 1
    print("VSIX 校验通过：%s（%d 个条目，解压后 %d 字节）" % (path, len(names), size))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", metavar="VSIX", help="校验已生成的 vsix")
    parser.add_argument("--output", metavar="PATH", help="输出路径")
    args = parser.parse_args()
    if args.check:
        return check(os.path.abspath(args.check))
    manifest = load_manifest()
    output = args.output or os.path.join(
        ROOT, "dist", "rill-dsl-%s.vsix" % manifest["version"]
    )
    build(os.path.abspath(output))
    print("已生成 %s" % output)
    return check(os.path.abspath(output))


if __name__ == "__main__":
    sys.exit(main())

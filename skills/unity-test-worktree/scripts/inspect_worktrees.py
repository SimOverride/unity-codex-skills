#!/usr/bin/env python3
"""只读比较同一 Git 仓库中不同工作树的当前可见内容。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys


class InspectionError(Exception):
    """当前条件不足以生成可信的内容比对。"""


def git(root: Path, *args: str) -> bytes:
    # 避免调用方的仓库重定向影响 -C 指定的身份，禁用可选索引写入。
    redirects = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR")
    if any(os.environ.get(key) for key in redirects):
        raise InspectionError("检测到 Git 仓库重定向环境变量，请在无重定向的终端运行。")
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, env=env, timeout=60
    )
    if result.returncode:
        raise InspectionError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def identity(value: str) -> dict:
    root = Path(value).resolve(strict=True)
    actual = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if root != actual:
        raise InspectionError(f"请传入仓库根而非子目录：{actual}")
    common = os.fsdecode(git(root, "rev-parse", "--git-common-dir")).strip()
    return {"root": root, "common": (root / common).resolve()}


def state(root: Path) -> tuple[bytes, bytes]:
    return (
        git(root, "rev-parse", "--verify", "HEAD"),
        git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"),
    )


def inventory(root: Path) -> list[str]:
    index = git(root, "ls-files", "--stage", "-z")
    for item in index.split(b"\0"):
        if not item:
            continue
        fields, raw_name = item.split(b"\t", 1)
        mode, _, stage = fields.split()
        if stage != b"0":
            raise InspectionError(f"存在未解决的合并冲突：{os.fsdecode(raw_name)}")
        if mode in (b"160000", b"120000"):
            raise InspectionError(f"需单独核对的子模块或符号链接：{os.fsdecode(raw_name)}")
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({os.fsdecode(item) for item in names.split(b"\0") if item})


def fingerprint(info: os.stat_result) -> tuple:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode


def file_digest(root: Path, name: str) -> str | None:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise InspectionError(f"路径不在工作树内：{name}")
    path = root
    # 拒绝父级目录联接和符号链接，不能顺着链接读取树外文件。
    for part in relative.parts:
        path /= part
        try:
            info = path.lstat()
        except FileNotFoundError:
            return None
        reparse = getattr(info, "st_file_attributes", 0) & 0x400
        if stat.S_ISLNK(info.st_mode) or reparse:
            raise InspectionError(f"需单独核对的链接或重解析点：{name}")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise InspectionError(f"不是普通文件，无法比较：{name}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if fingerprint(before) != fingerprint(path.stat()):
        raise InspectionError(f"读取过程中内容发生变化：{name}")
    return digest.hexdigest()


def snapshot(repo: dict) -> dict:
    root = repo["root"]
    before = state(root)
    names = inventory(root)
    files = {}
    for name in names:
        digest = file_digest(root, name)
        if digest is not None:
            files[name] = digest
    if before != state(root) or names != inventory(root):
        raise InspectionError("扫描期间 Git 状态或文件清单改变，请协调使用者后重新核对。")
    # 摘要包含路径，重命名和内容相同但位置不同仍会形成差异。
    encoded = json.dumps(files, ensure_ascii=True, sort_keys=True).encode("utf-8")
    return {
        "root": str(root),
        "commonGitDir": str(repo["common"]),
        "head": before[0].decode().strip(),
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD").decode().strip(),
        "statusEntries": [os.fsdecode(item) for item in before[1].split(b"\0") if item],
        "fileCount": len(files),
        "contentSha256": hashlib.sha256(encoded).hexdigest(),
        "files": files,
    }


def inspect(source: str, target: str | None = None) -> tuple[dict, int]:
    src = identity(source)
    dst = identity(target) if target else None
    if dst and (src["root"] == dst["root"] or src["common"] != dst["common"]):
        raise InspectionError("目标必须是同一仓库的另一个工作树，不能是源目录或独立克隆。")
    report = {
        "schemaVersion": 1,
        "scope": "Git 已跟踪文件及非忽略未跟踪文件的字节与路径",
        "limitations": [
            "未获取占用锁，不能证明 Unity 或其他任务未使用目标。",
            "不验证忽略文件、外部依赖、LFS 下载状态、权限与 Unity 环境。",
            "非原子快照，仍需独占协调和运行前后核对。",
        ],
        "source": snapshot(src),
    }
    if not dst:
        return report, 0
    report["target"] = snapshot(dst)
    # 目标扫描期间源工作树可能变化，再核对源内容而非仅查看 dirty 标志。
    if snapshot(src) != report["source"]:
        raise InspectionError("比较期间源工作树内容发生变化，结果无效。")
    left, right = report["source"]["files"], report["target"]["files"]
    differences = {
        "onlySource": sorted(left.keys() - right.keys()),
        "onlyTarget": sorted(right.keys() - left.keys()),
        "changed": sorted(name for name in left.keys() & right.keys() if left[name] != right[name]),
    }
    report["differences"] = differences
    report["sameVisibleContent"] = not any(differences.values())
    return report, 0 if report["sameVisibleContent"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="开发仓库根目录")
    parser.add_argument("--target", help="可选：同一仓库的测试工作树根目录")
    args = parser.parse_args()
    try:
        report, code = inspect(args.source, args.target)
    except (InspectionError, OSError, subprocess.TimeoutExpired) as error:
        report, code = {"error": str(error), "sameVisibleContent": None}, 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())

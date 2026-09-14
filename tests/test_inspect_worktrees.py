"""用真实 Git 工作树验证内容核对与拒绝分支，不启动 Unity。"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills/unity-test-worktree/scripts/inspect_worktrees.py"
spec = importlib.util.spec_from_file_location("inspect_worktrees", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        scratch = REPO / "work" / "tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.base = Path(self.temp.name).resolve()
        self.assertTrue(self.base.is_relative_to(scratch.resolve()))
        self.source = self.base / "源 项目"
        self.target = self.base / "测试 树"
        self.source.mkdir()
        self.git(self.source, "init", "-b", "main")
        self.git(self.source, "config", "user.name", "Skill Test")
        self.git(self.source, "config", "user.email", "skill-test@example.invalid")
        self.git(self.source, "config", "core.autocrlf", "false")
        self.git(self.source, "config", "commit.gpgsign", "false")
        (self.source / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        (self.source / "数据 文件.txt").write_bytes(b"original\r\n")
        (self.source / "数据 文件.txt.meta").write_bytes(b"guid: test\r\n")
        self.git(self.source, "add", ".")
        self.git(self.source, "commit", "-m", "fixture")
        self.git(self.source, "worktree", "add", "-b", "agent-test", str(self.target))

    def tearDown(self):
        # 仅删除 setUp 创建并校验过的临时 Git 目录，不涉及 Unity 项目。
        self.temp.cleanup()

    @staticmethod
    def git(path, *args):
        result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, check=True)
        return result.stdout

    def compare(self):
        return module.inspect(str(self.source), str(self.target))

    def test_equal_and_read_only(self):
        before = self.git(self.source, "status", "--porcelain=v1", "-z")
        report, code = self.compare()
        self.assertEqual(code, 0)
        self.assertTrue(report["sameVisibleContent"])
        self.assertEqual(before, self.git(self.source, "status", "--porcelain=v1", "-z"))

    def test_dirty_source_and_expected_dirty_target(self):
        for root in (self.source, self.target):
            (root / "数据 文件.txt").write_bytes(b"changed\r\n")
            (root / "新 资源.meta").write_bytes(b"new meta")
        report, code = self.compare()
        self.assertEqual(code, 0)
        self.assertTrue(report["source"]["statusEntries"])

    def test_modified_deleted_untracked_and_meta(self):
        (self.source / "数据 文件.txt").unlink()
        (self.source / "数据 文件.txt.meta").write_bytes(b"changed guid")
        (self.source / "新资源.asset").write_bytes(b"new")
        report, code = self.compare()
        self.assertEqual(code, 1)
        self.assertIn("数据 文件.txt", report["differences"]["onlyTarget"])
        self.assertIn("数据 文件.txt.meta", report["differences"]["changed"])
        self.assertIn("新资源.asset", report["differences"]["onlySource"])

    def test_ignored_files_excluded_tracked_ignored_included(self):
        (self.source / "ignored").mkdir()
        (self.source / "ignored/cache").write_bytes(b"cache")
        self.assertEqual(self.compare()[1], 0)
        self.git(self.source, "add", "-f", "ignored/cache")
        self.assertEqual(self.compare()[1], 1)

    def test_staged_content_not_working_content(self):
        (self.source / "数据 文件.txt").write_bytes(b"staged")
        self.git(self.source, "add", ".")
        (self.source / "数据 文件.txt").write_bytes(b"original\r\n")
        self.assertEqual(self.compare()[1], 0)

    def test_line_endings_are_content(self):
        (self.target / "数据 文件.txt").write_bytes(b"original\n")
        self.assertEqual(self.compare()[1], 1)

    def test_source_is_not_target(self):
        with self.assertRaises(module.InspectionError):
            module.inspect(str(self.source), str(self.source))

    def test_independent_clone_rejected(self):
        clone = self.base / "clone"
        self.git(self.source, "clone", str(self.source), str(clone))
        with self.assertRaises(module.InspectionError):
            module.inspect(str(self.source), str(clone))

    def test_submodule_entry_rejected(self):
        head = self.git(self.source, "rev-parse", "HEAD").decode().strip()
        self.git(self.source, "update-index", "--add", "--cacheinfo", "160000", head, "dependency")
        with self.assertRaises(module.InspectionError):
            self.compare()

    def test_symlink_entry_rejected(self):
        blob = self.git(self.source, "rev-parse", "HEAD:数据 文件.txt").decode().strip()
        self.git(self.source, "update-index", "--add", "--cacheinfo", "120000", blob, "link")
        with self.assertRaises(module.InspectionError):
            self.compare()

    def test_changed_state_during_scan_rejected(self):
        real_state = module.state
        count = 0

        def changing_state(root):
            nonlocal count
            count += 1
            if count == 2:
                (root / "concurrent.txt").write_bytes(b"another task")
            return real_state(root)

        with mock.patch.object(module, "state", side_effect=changing_state):
            with self.assertRaises(module.InspectionError):
                self.compare()

    def test_cli_success_difference_and_error(self):
        def run(*args):
            result = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True)
            return result.returncode, json.loads(result.stdout)

        self.assertEqual(run("--source", str(self.source))[0], 0)
        (self.target / "extra.txt").write_bytes(b"extra")
        self.assertEqual(run("--source", str(self.source), "--target", str(self.target))[0], 1)
        code, report = run("--source", str(self.base / "missing"))
        self.assertEqual(code, 2)
        self.assertIsNone(report["sameVisibleContent"])


if __name__ == "__main__":
    unittest.main()

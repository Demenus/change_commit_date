from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from io import StringIO
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from ccd.cli import run
from ccd.git import GitError, Repository


class GitIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.source_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.tempdir.name
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        self.commit("base", "2024-01-01T09:00:00+00:00")
        self.commit("one", "2024-01-01T10:12:03+00:00")
        self.commit("two", "2024-01-01T12:32:04+00:00")
        self.commit("three", "2024-01-01T20:45:05+00:00")
        self.main_branch = self.git("symbolic-ref", "--short", "HEAD")

    def tearDown(self):
        self.tempdir.cleanup()
        self.source_dir.cleanup()

    def git(self, *args, env=None):
        command = ["git", "-C", self.repo_path, *args]
        return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=env, check=True).stdout.strip()

    def commit(self, name, date):
        Path(self.repo_path, name).write_text(name, encoding="utf-8")
        self.git("add", name)
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
        self.git("-c", "commit.gpgSign=false", "commit", "-qm", name, env=env)

    def invoke(self, *args):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = run(args)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_preview_does_not_change_head(self):
        before = self.git("rev-parse", "HEAD")
        status, stdout, _ = self.invoke(
            "schedule", "--path", self.repo_path, "--window", "18:00-03:00",
            "--range", "HEAD~3..HEAD~1",
        )
        self.assertEqual(status, 0)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertIn("Preview only", stdout)
        self.assertIn("18:12:03", stdout)

    def test_apply_rewrites_author_and_committer_dates(self):
        status, _, stderr = self.invoke(
            "schedule", "--path", self.repo_path, "--window", "18:00-03:00",
            "--range", "HEAD~3..HEAD~1", "--apply",
        )
        self.assertEqual((status, stderr), (0, ""))
        dates = {
            line.rsplit("|", 1)[1]: line.rsplit("|", 1)[0]
            for line in self.git("log", "--format=%aI|%cI|%s").splitlines()
        }
        self.assertEqual(dates["one"], "2024-01-01T18:12:03Z|2024-01-01T18:12:03Z")
        self.assertEqual(dates["two"], "2024-01-01T20:32:04Z|2024-01-01T20:32:04Z")

    def test_hash_file_allows_comments_and_non_contiguous_selection(self):
        first = self.git("rev-parse", "HEAD~2")
        last = self.git("rev-parse", "HEAD")
        source = Path(self.source_dir.name, "hashes.txt")
        source.write_text(f"# selected commits\n{last}\n\n{first} # an inline comment\n", encoding="utf-8")
        status, stdout, _ = self.invoke(
            "schedule", "--path", self.repo_path, "--window", "18:00-03:00",
            "--commits-file", str(source),
        )
        self.assertEqual(status, 0)
        self.assertLess(stdout.find(first[:8]), stdout.find(last[:8]))

    def test_rejects_dirty_worktree_and_unknown_hash(self):
        Path(self.repo_path, "dirty").write_text("dirty", encoding="utf-8")
        status, _, stderr = self.invoke(
            "schedule", "--path", self.repo_path, "--window", "18:00-03:00", "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(status, 2)
        self.assertIn("not clean", stderr)
        os.unlink(Path(self.repo_path, "dirty"))
        source = Path(self.source_dir.name, "bad-hashes.txt")
        source.write_text("does-not-exist\n", encoding="utf-8")
        status, _, stderr = self.invoke(
            "schedule", "--path", self.repo_path, "--window", "18:00-03:00", "--commits-file", str(source)
        )
        self.assertEqual(status, 2)
        self.assertIn("fatal", stderr)

    def test_rejects_commit_outside_head_history(self):
        self.git("branch", "side", "HEAD~3")
        self.git("checkout", "-q", "side")
        self.commit("side", "2024-01-02T10:00:00+00:00")
        side = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", self.main_branch)
        with self.assertRaises(GitError):
            Repository(self.repo_path).select_linear_commits([side])

    def test_rejects_merges(self):
        self.git("branch", "topic", "HEAD~2")
        self.git("checkout", "-q", "topic")
        self.commit("topic", "2024-01-02T10:00:00+00:00")
        self.git("checkout", "-q", self.main_branch)
        self.git("-c", "commit.gpgSign=false", "merge", "--no-ff", "topic", "-m", "merge topic")
        with self.assertRaisesRegex(GitError, "Merge commits"):
            Repository(self.repo_path).select_linear_commits([self.git("rev-parse", "HEAD~1")])

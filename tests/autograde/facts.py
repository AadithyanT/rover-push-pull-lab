"""Ground truth about the student's repository. Read-only: never changes the repo and never uses the network."""
from __future__ import annotations

import os
import re
import subprocess
from typing import List, NamedTuple, Optional, Set, Tuple

STAFF_SUBJECT = "chore: add lab assignment and grader"
WEB1_SUBJECT = "docs: add team contact line"
WEB2_SUBJECT = "docs: add field team note"
LOCAL_SUBJECT = "docs: log left turn calibration"
FEATURE_SUBJECT = "feat(control): add turn calibration stub"
FEATURE_BRANCH = "feature/turn-calibration"
FEATURE_FILE = "calibrate_turn.py"
CONTACT_LINE = "Contact the team: rover-team@example.com"
NOTE_LINE = "- Field team: log every test run in CHANGELOG.md."
GITHUB_COMMITTER_EMAIL = "noreply@github.com"
COURSE_SLUG = "qbit-glitch/26ra2308-gitlab-9-rover-push-pull-lab"  # lower case; the course repository students start from
GIT_TIMEOUT = 60
SLUG_RE = re.compile(r"github\.com[:/]([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


class GitError(RuntimeError):
    """Raised when the repository is not set up the way the grader expects."""


class Commit(NamedTuple):
    """A commit of the starting history."""

    sha: str
    author: str
    email: str
    subject: str


class Added(NamedTuple):
    """A commit that main gained on top of the starting commit."""

    sha: str
    author: str
    email: str
    committer: str
    committer_email: str
    subject: str
    parents: List[str]


def slug_of(url: str) -> str:
    """'owner/repo' (lower case) of a GitHub address in any of its forms ('' if it is not a GitHub address)."""
    match = SLUG_RE.search(url.strip())
    return f"{match.group(1)}/{match.group(2)}".lower() if match else ""


def run_git_rc(repo: str, *args: str) -> Tuple[int, str]:
    """Run git in 'repo' and return (exit code, stdout); a git call that hangs is stopped and reported as 124."""
    env = dict(os.environ, LC_ALL="C", GIT_PAGER="cat", GIT_TERMINAL_PROMPT="0")
    try:
        proc = subprocess.run(["git", *args], cwd=repo, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return 124, ""
    return proc.returncode, proc.stdout


def run_git(repo: str, *args: str) -> str:
    """Run git in 'repo' and return stdout ('' on failure)."""
    return run_git_rc(repo, *args)[1]


class Facts:
    """Everything the grader needs to know about the repository."""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        if run_git_rc(repo, "rev-parse", "--verify", "-q", "refs/heads/main^{commit}")[0] != 0:
            raise GitError("branch main not found. Run the grader inside your clone of the lab repository.")
        raw = run_git(repo, "log", "refs/heads/main", "--format=%H%x1f%an%x1f%ae%x1f%s")
        log = [Commit(*line.split("\x1f")) for line in raw.splitlines() if line.count("\x1f") == 3]
        staff = [c for c in log if c.subject == STAFF_SUBJECT]
        if not staff:
            raise GitError(f"the starting commit '{STAFF_SUBJECT}' is not in the history of main. "
                           "Run the grader inside your clone of the lab repository (made with 'git clone').")
        self.base: str = staff[-1].sha
        raw = run_git(repo, "log", self.base, "--format=%H%x1f%an%x1f%ae%x1f%s")
        self.published: List[Commit] = [Commit(*line.split("\x1f")) for line in raw.splitlines() if line.count("\x1f") == 3]

    # -- the starting history ------------------------------------------------------------
    def published_emails(self) -> Set[str]:
        """E-mail addresses of the people who wrote the starting history."""
        return {c.email.lower() for c in self.published}

    def published_names(self) -> Set[str]:
        """Names of the people who wrote the starting history."""
        return {c.author.lower() for c in self.published}

    # -- the student's live repository ---------------------------------------------------
    def config_value(self, key: str) -> str:
        """Value of a repository-local config key ('' if unset)."""
        return run_git(self.repo, "config", "--local", "--get", key).strip()

    def remote_url(self, name: str) -> str:
        """The address stored for remote 'name' in this repository's own config ('' if there is none)."""
        return self.config_value(f"remote.{name}.url")

    def branch_config(self, branch: str) -> Tuple[str, str]:
        """(remote, merge ref) a local branch is set up to track ('' for unset values)."""
        return self.config_value(f"branch.{branch}.remote"), self.config_value(f"branch.{branch}.merge")

    def rev(self, ref: str) -> str:
        """Full SHA of 'ref' ('' if it does not name a commit)."""
        return run_git(self.repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}").strip()

    def commit_exists(self, token: str) -> bool:
        """True if 'token' names a commit object in this repository."""
        return run_git_rc(self.repo, "cat-file", "-e", f"{token}^{{commit}}")[0] == 0

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """True if commit 'ancestor' is 'descendant' itself or part of its history."""
        return run_git_rc(self.repo, "merge-base", "--is-ancestor", ancestor, descendant)[0] == 0

    def file_at(self, ref: str, path: str) -> Optional[str]:
        """Content of 'path' at 'ref' (None if absent)."""
        code, out = run_git_rc(self.repo, "show", f"{ref}:{path}")
        return out if code == 0 else None

    def reflog(self, ref: str) -> List[str]:
        """Reflog messages of 'ref', newest first (empty if there is no reflog)."""
        return run_git(self.repo, "log", "-g", "--format=%gs", ref, "--").splitlines()

    def head_reflog(self) -> List[str]:
        """HEAD reflog messages, newest first."""
        return self.reflog("HEAD")

    def parents(self, sha: str) -> List[str]:
        """Full SHAs of the parents of 'sha' (empty for a root commit or an unknown commit)."""
        return run_git(self.repo, "show", "-s", "--format=%P", sha).split()

    def subject(self, sha: str) -> str:
        """Subject line of commit 'sha' ('' if unknown)."""
        return run_git(self.repo, "show", "-s", "--format=%s", sha).strip()

    def main_tip(self) -> str:
        """Full SHA of the local branch main."""
        return self.rev("refs/heads/main")

    def added(self) -> List[Added]:
        """The commits main gained on top of the starting commit, following first parents, oldest first."""
        shas = run_git(self.repo, "rev-list", "--first-parent", "--reverse", f"{self.base}..refs/heads/main").split()
        out: List[Added] = []
        for sha in shas:
            fields = run_git(self.repo, "show", "-s", "--format=%an%x1f%ae%x1f%cn%x1f%ce%x1f%s%x1f%P", sha)
            parts = fields.rstrip("\n").split("\x1f")
            if len(parts) == 6:
                out.append(Added(sha, parts[0], parts[1], parts[2], parts[3], parts[4], parts[5].split()))
        return out

    def web_commit(self, subject: str) -> Optional[Added]:
        """The commit on main with this subject that GitHub itself made (committer noreply@github.com), if any."""
        for commit in self.added():
            if commit.subject == subject and commit.committer_email.lower() == GITHUB_COMMITTER_EMAIL \
                    and len(commit.parents) == 1:
                return commit
        return None

    def my_commit(self, subject: str) -> Optional[Added]:
        """The commit on main with this subject that the student made (committer is not GitHub), if any."""
        for commit in reversed(self.added()):
            if commit.subject == subject and commit.committer_email.lower() != GITHUB_COMMITTER_EMAIL:
                return commit
        return None

    def merges_above_base(self) -> int:
        """Number of merge commits on main above the starting commit."""
        out = run_git(self.repo, "rev-list", "--count", "--merges", f"{self.base}..refs/heads/main").strip()
        return int(out) if out.isdigit() else -1

    def commits_above_base(self) -> int:
        """Number of commits on main above the starting commit."""
        out = run_git(self.repo, "rev-list", "--count", f"{self.base}..refs/heads/main").strip()
        return int(out) if out.isdigit() else -1

    def working_tree_clean(self) -> bool:
        """True when 'git status --porcelain' prints nothing and no merge or rebase is in progress."""
        clean = run_git(self.repo, "status", "--porcelain").strip() == ""
        merging = run_git_rc(self.repo, "rev-parse", "-q", "--verify", "MERGE_HEAD")[0] == 0
        rebasing = any(os.path.exists(os.path.join(self.repo, run_git(self.repo, "rev-parse", "--git-path", name).strip()))
                       for name in ("rebase-merge", "rebase-apply"))
        return clean and not merging and not rebasing

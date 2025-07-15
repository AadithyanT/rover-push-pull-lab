"""Graders for the five tasks of the Push and Pull lab."""
from __future__ import annotations

import re
from typing import Dict, Optional

from .context import Ctx
from .facts import (
    COURSE_SLUG, CONTACT_LINE, FEATURE_BRANCH, FEATURE_FILE, FEATURE_SUBJECT, LOCAL_SUBJECT, STAFF_SUBJECT,
    WEB1_SUBJECT, WEB2_SUBJECT, slug_of,
)
from .framework import Task
from .textutil import (
    BranchRow, branch_names, get_answer, get_answer_int, get_answer_sha, oneline_entries, parse_branch_list, parse_status,
    same_sha, sha_matches, strip_decoration,
)

PLACEHOLDER_NAMES = {"", "your full name", "your name"}
PLACEHOLDER_EMAILS = {"", "your.email@example.com"}
TREE_ALIAS = "log --oneline --graph --decorate --all"
GRAPH_NODE_RE = re.compile(r"(?m)^[ |\\/]*\*")
FORK_OR_JOIN_RE = re.compile(r"(?m)^\s*[|\\/]")
REMOTE_LINE_RE = re.compile(r"(?m)^(\S+)\s+(\S+)\s+\((fetch|push)\)\s*$")
RANGE_RE = re.compile(r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s+main\s+->\s+origin/main\s*$")
PUSH_RANGE_RE = re.compile(r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s+main\s+->\s+main\s*$")
UPDATING_RE = re.compile(r"(?m)^Updating ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s*$")
COMMIT_LINE_RE = re.compile(r"\[main (?:\(root-commit\) )?([0-9a-f]{7,40})\] " + re.escape(LOCAL_SUBJECT))
TO_LINE_RE = re.compile(r"(?m)^To (\S+)\s*$")


def _line_with(text: str, *needles: str) -> bool:
    """True when one line of the text holds every needle."""
    return any(all(n in line for n in needles) for line in text.split("\n"))


def _tracks(rest: str, upstream: str) -> bool:
    """True when the rest of a 'git branch -vv' row names this upstream in brackets, as in '[origin/main]'."""
    return re.search(r"\[" + re.escape(upstream) + r"[\]:]", rest) is not None


def parse_remotes(text: str) -> Dict[str, Dict[str, str]]:
    """Read 'git remote -v' output into {remote name: {'fetch': url, 'push': url}}."""
    remotes: Dict[str, Dict[str, str]] = {}
    for name, url, kind in REMOTE_LINE_RE.findall(text):
        remotes.setdefault(name, {})[kind] = url
    return remotes


def pasted_origin_slug(ctx: Ctx) -> str:
    """'owner/repo' of the origin remote the student pasted in step 1.1 ('' if there is none)."""
    return slug_of(parse_remotes(ctx.step("1.1")).get("origin", {}).get("fetch", ""))


def student_slug(ctx: Ctx) -> str:
    """'owner/repo' of the student's own repository: from the clone's config when it can be read, else from 1.1."""
    live = slug_of(ctx.facts.remote_url("origin")) if ctx.repo_mode else ""
    return live if live and live != COURSE_SLUG else pasted_origin_slug(ctx)


def _to_slug(text: str) -> str:
    """'owner/repo' named by the first 'To <address>' line of a pasted push ('' if there is none)."""
    match = TO_LINE_RE.search(text)
    return slug_of(match.group(1)) if match else ""


def _branch_row(text: str, name: str) -> Optional[BranchRow]:
    """The row of 'git branch' output for one branch name (None if it is not listed)."""
    return next((r for r in parse_branch_list(text) if r.name == name), None)


# -- Task 1 -----------------------------------------------------------------
def grade_task1(ctx: Ctx) -> Task:
    """Task 1: connect the clone to your own GitHub repository and push main."""
    t = Task(1, "Connect to GitHub", 20, ctx.repo_mode)
    f = ctx.facts
    remotes = parse_remotes(ctx.step("1.1"))
    origin, upstream = remotes.get("origin", {}), remotes.get("upstream", {})
    mine = slug_of(origin.get("fetch", ""))
    t.check(2, "1.1 remote -v: upstream (fetch and push) is the course repository",
            lambda: slug_of(upstream.get("fetch", "")) == COURSE_SLUG and slug_of(upstream.get("push", "")) == COURSE_SLUG)
    t.check(3, "1.1 remote -v: origin (fetch and push) is your own GitHub repository, not the course repository",
            lambda: bool(mine) and mine != COURSE_SLUG and slug_of(origin.get("push", "")) == mine)
    t.check(1, "1.1 remote -v lists exactly two remotes, origin and upstream", lambda: set(remotes) == {"origin", "upstream"})
    s12 = ctx.step("1.2")
    t.check(2, "1.2 push output: '* [new branch]  main -> main'",
            lambda: re.search(r"\* \[new branch\]\s+main -> main", s12) is not None)
    t.check(2, "1.2 push output: branch 'main' set up to track 'origin/main' (this is what -u does)",
            lambda: re.search(r"(?i)branch 'main' set up to track (?:remote branch 'main' from 'origin'|'origin/main')", s12)
            is not None)
    t.check(1, "1.2 the push went to your own repository (the 'To ...' line names the same repository as origin)",
            lambda: bool(student_slug(ctx)) and _to_slug(s12) == student_slug(ctx))
    s13 = ctx.step("1.3")
    row = _branch_row(s13, "main")
    t.check(3, "1.3 branch -vv: main is checked out, tracks [origin/main] and sits on 'chore: add lab assignment and grader'",
            lambda: row is not None and row.current and _tracks(row.rest, "origin/main") and STAFF_SUBJECT in row.rest)
    t.check(1, "ANSWER-1 is upstream (the remote that points to the course repository)",
            lambda: get_answer(ctx.text, 1).strip("`'\" ").lower() == "upstream")
    name, email = f.config_value("user.name"), f.config_value("user.email")
    t.check(2, "live repo: your identity is set in this clone (not a placeholder, not a teammate's)",
            lambda: name.lower() not in PLACEHOLDER_NAMES and "@" in email and email.lower() not in PLACEHOLDER_EMAILS
            and name.lower() not in f.published_names() and email.lower() not in f.published_emails(),
            needs_repo=True)
    url = f.remote_url("origin") if ctx.repo_mode else ""
    t.check(1, "live repo: remote origin is a GitHub address of your own (not the course repository) and matches the pasted one",
            lambda: bool(slug_of(url)) and slug_of(url) != COURSE_SLUG and (not mine or slug_of(url) == mine),
            needs_repo=True,
            why=lambda: "origin must be your own GitHub repository (git@github.com:<you>/<repo>.git)")
    t.check(1, "live repo: alias.tree is set to 'log --oneline --graph --decorate --all'",
            lambda: f.config_value("alias.tree") == TREE_ALIAS, needs_repo=True)
    t.check(1, "live repo: main tracks origin/main, your own repository (branch.main.remote and branch.main.merge are set)",
            lambda: f.branch_config("main") == ("origin", "refs/heads/main") and bool(f.rev("refs/remotes/origin/main"))
            and slug_of(url) not in ("", COURSE_SLUG),
            needs_repo=True, why=lambda: "main has no upstream: push with -u")
    return t


# -- Task 2 -----------------------------------------------------------------
def grade_task2(ctx: Ctx) -> Task:
    """Task 2: fetch and look, then pull (the change was made on github.com)."""
    t = Task(2, "Fetch, then pull", 25, ctx.repo_mode)
    f = ctx.facts
    web1 = f.web_commit(WEB1_SUBJECT) if ctx.repo_mode else None
    s21 = ctx.step("2.1")
    fetched = RANGE_RE.search(s21)
    t.check(4, "2.1 fetch output: '<old>..<new>  main -> origin/main'", lambda: fetched is not None)
    t.check(2, "live repo: the fetched range starts at the course's last commit and ends at the commit made on GitHub",
            lambda: fetched is not None and web1 is not None and sha_matches(fetched.group(1), f.base)
            and sha_matches(fetched.group(2), web1.sha), needs_repo=True,
            why=lambda: f"no commit '{WEB1_SUBJECT}' made on github.com is the first commit above the starting commit")
    s22 = ctx.step("2.2")
    t.check(4, "2.2 status: Your branch is behind 'origin/main' by 1 commit, and can be fast-forwarded.",
            lambda: re.search(r"behind 'origin/main' by 1 commit", s22) is not None and "can be fast-forwarded" in s22)
    s23 = ctx.step("2.3")
    t.check(3, "2.3 diff shows README.md and the added line '+Contact the team: rover-team@example.com'",
            lambda: "diff --git a/README.md b/README.md" in s23 and f"+{CONTACT_LINE}" in s23.split("\n"))
    s24 = ctx.step("2.4")
    updating = UPDATING_RE.search(s24)
    t.check(3, "2.4 pull output: 'Updating <old>..<new>', 'Fast-forward' and README.md changed",
            lambda: updating is not None and "Fast-forward" in s24 and re.search(r"README\.md \| +\d+ \++", s24) is not None)
    t.check(1, "2.4 the range is the one that fetch printed in 2.1",
            lambda: updating is not None and fetched is not None and sha_matches(updating.group(1), fetched.group(1))
            and sha_matches(updating.group(2), fetched.group(2)))
    added = f.added() if ctx.repo_mode else []
    t.check(3, "live repo: the first commit main gained is 'docs: add team contact line', made on GitHub, and README.md has the line",
            lambda: bool(added) and web1 is not None and added[0].sha == web1.sha
            and CONTACT_LINE in (f.file_at(web1.sha, "README.md") or "").splitlines(), needs_repo=True)
    t.check(2, "live repo: HEAD's reflog records the pull ('pull origin main: Fast-forward')",
            lambda: any(m.startswith("pull") and m.endswith("Fast-forward") for m in f.head_reflog()), needs_repo=True)
    t.check(2, "live repo: origin/main's reflog records a fetch ('fetch origin: fast-forward')",
            lambda: any(m.startswith("fetch") and m.endswith("fast-forward") for m in f.reflog("refs/remotes/origin/main")),
            needs_repo=True, why=lambda: "no 'git fetch origin' was run before the pull")
    t.check(1, "live repo: no merge commit was made (a pull that can fast-forward only moves main)",
            lambda: web1 is not None and f.merges_above_base() == 0, needs_repo=True)
    return t


# -- Task 3 -----------------------------------------------------------------
def grade_task3(ctx: Ctx) -> Task:
    """Task 3: a rejected push, solved by rebasing on the GitHub commit, then pushed."""
    t = Task(3, "A rejected push", 30, ctx.repo_mode)
    f = ctx.facts
    mine = student_slug(ctx)
    s31 = ctx.step("3.1")
    first = COMMIT_LINE_RE.search(s31)
    t.check(3, "3.1 commit output: '[main <sha>] docs: log left turn calibration' and 1 file changed",
            lambda: first is not None and re.search(r"\b1 file changed", s31) is not None)
    s32 = ctx.step("3.2")
    t.check(3, "3.2 push output: '! [rejected]  main -> main (fetch first)'",
            lambda: re.search(r"! \[rejected\]\s+main -> main \(fetch first\)", s32) is not None)
    t.check(2, "3.2 push output: 'error: failed to push some refs'", lambda: "error: failed to push some refs" in s32)
    t.check(1, "3.2 the push was aimed at your own repository",
            lambda: bool(mine) and _to_slug(s32) == mine)
    s33 = ctx.step("3.3")
    t.check(3, "3.3 rebase output: 'Successfully rebased and updated refs/heads/main.'",
            lambda: "Successfully rebased and updated refs/heads/main." in s33)
    t.check(2, "3.3 fetch line inside the output: '<old>..<new>  main -> origin/main'",
            lambda: RANGE_RE.search(s33) is not None)
    s34 = ctx.step("3.4")
    entries = oneline_entries(s34)
    head_at = next((i for i, e in enumerate(entries) if "HEAD -> main" in e.subject), -1)
    origin_at = next((i for i, e in enumerate(entries) if "origin/main" in e.subject), -1)
    t.check(2, "3.4 graph: your commit 'docs: log left turn calibration' is at HEAD -> main, just above origin/main "
               "('docs: add field team note')",
            lambda: 0 <= head_at < origin_at and strip_decoration(entries[head_at].subject) == LOCAL_SUBJECT
            and strip_decoration(entries[origin_at].subject) == WEB2_SUBJECT)
    t.check(2, "3.4 graph is one straight line (no fork or join: no line starts with '|', '\\' or '/')",
            lambda: len(entries) >= 4 and GRAPH_NODE_RE.search(s34) is not None and FORK_OR_JOIN_RE.search(s34) is None)
    s35 = ctx.step("3.5")
    pushed = PUSH_RANGE_RE.search(s35)
    t.check(3, "3.5 push output: '<old>..<new>  main -> main' (accepted), and it is not rejected",
            lambda: pushed is not None and "! [rejected]" not in s35)
    web_sha = entries[origin_at].sha if origin_at >= 0 else ""
    t.check(2, "ANSWER-2 is the commit number printed next to origin/main in 3.4 (the commit made on GitHub)",
            lambda: bool(web_sha) and same_sha(get_answer_sha(ctx.text, 2), web_sha))
    web2 = f.web_commit(WEB2_SUBJECT) if ctx.repo_mode else None
    local = f.my_commit(LOCAL_SUBJECT) if ctx.repo_mode else None
    t.check(3, "live repo: main's newest commit is your 'docs: log left turn calibration', its parent is the GitHub commit "
               "'docs: add field team note', and its number is not the one printed in 3.1 (the rebase made a new commit)",
            lambda: local is not None and web2 is not None and f.added()[-1].sha == local.sha
            and local.parents == [web2.sha] and first is not None and not sha_matches(first.group(1), local.sha),
            needs_repo=True,
            why=lambda: "expected main = ... -> 'docs: add field team note' (GitHub) -> your commit, with a new number after the rebase")
    t.check(1, "live repo: the commit printed in 3.1 is no longer part of main (the rebase replaced it)",
            lambda: first is not None and f.commit_exists(first.group(1)) and not f.is_ancestor(first.group(1), f.main_tip()),
            needs_repo=True)
    t.check(1, "live repo: history above the course's last commit has no merge commit (a rebase keeps one straight line)",
            lambda: local is not None and f.merges_above_base() == 0, needs_repo=True)
    t.check(1, "live repo: origin/main is your rebased commit (the second push really reached GitHub)",
            lambda: local is not None and f.rev("refs/remotes/origin/main") == local.sha,
            needs_repo=True)
    t.check(1, "live repo: ANSWER-2 is the commit 'docs: add field team note' that GitHub made",
            lambda: web2 is not None and sha_matches(get_answer_sha(ctx.text, 2), web2.sha), needs_repo=True)
    return t


# -- Task 4 -----------------------------------------------------------------
def grade_task4(ctx: Ctx) -> Task:
    """Task 4: publish a feature branch with tracking and look at the remote."""
    t = Task(4, "Publish a feature branch", 15, ctx.repo_mode)
    f = ctx.facts
    mine = student_slug(ctx)
    s41 = ctx.step("4.1")
    branch = re.escape(FEATURE_BRANCH)
    t.check(2, "4.1 push output: '* [new branch]  feature/turn-calibration -> feature/turn-calibration'",
            lambda: re.search(r"\* \[new branch\]\s+" + branch + " -> " + branch, s41) is not None)
    t.check(2, "4.1 push output: branch 'feature/turn-calibration' set up to track 'origin/feature/turn-calibration'",
            lambda: re.search(r"(?i)branch '" + branch + r"' set up to track (?:remote branch '" + branch + r"' from 'origin'|'origin/"
                              + branch + "')", s41) is not None)
    s42 = ctx.step("4.2")
    feature, main = _branch_row(s42, FEATURE_BRANCH), _branch_row(s42, "main")
    t.check(2, "4.2 branch -vv: the checked-out feature branch tracks [origin/feature/turn-calibration] and shows its commit "
               "'feat(control): add turn calibration stub'",
            lambda: feature is not None and feature.current and _tracks(feature.rest, "origin/" + FEATURE_BRANCH)
            and FEATURE_SUBJECT in feature.rest)
    t.check(1, "4.2 branch -vv: main tracks [origin/main]", lambda: main is not None and _tracks(main.rest, "origin/main"))
    s43 = ctx.step("4.3")
    t.check(1, "4.3 remote show: the Fetch URL is your own repository",
            lambda: bool(mine) and any(line.strip().startswith("Fetch URL:") and slug_of(line) == mine for line in s43.split("\n")))
    t.check(1, "4.3 remote show: both main and feature/turn-calibration are listed as remote branches that are tracked",
            lambda: re.search(r"(?m)^\s+" + branch + r"\s+tracked\b", s43) is not None
            and re.search(r"(?m)^\s+main\s+tracked\b", s43) is not None)
    t.check(1, "4.3 remote show: 'Local refs configured for git push' lists feature/turn-calibration pushes to feature/turn-calibration",
            lambda: re.search(r"Local refs? configured for 'git push'", s43) is not None
            and re.search(branch + r"\s+pushes to\s+" + branch, s43) is not None)
    tip = f.rev(f"refs/heads/{FEATURE_BRANCH}") if ctx.repo_mode else ""
    t.check(2, "live repo: local branch feature/turn-calibration tracks origin/feature/turn-calibration",
            lambda: f.branch_config(FEATURE_BRANCH) == ("origin", f"refs/heads/{FEATURE_BRANCH}"), needs_repo=True,
            why=lambda: "the branch has no upstream: push it with -u")
    t.check(1, "live repo: its tip is on GitHub (origin/feature/turn-calibration is the same commit)",
            lambda: bool(tip) and f.rev(f"refs/remotes/origin/{FEATURE_BRANCH}") == tip, needs_repo=True)
    t.check(1, "live repo: the tip is 'feat(control): add turn calibration stub' and holds calibrate_turn.py",
            lambda: bool(tip) and f.file_at(tip, FEATURE_FILE) is not None
            and f.subject(tip) == FEATURE_SUBJECT, needs_repo=True)
    t.check(1, "live repo: the branch grew out of main (the commit under its tip is part of main)",
            lambda: bool(tip) and bool(f.parents(tip)) and f.is_ancestor(f.parents(tip)[0], f.main_tip()), needs_repo=True)
    return t


# -- Task 5 -----------------------------------------------------------------
def grade_task5(ctx: Ctx) -> Task:
    """Task 5: wrap up (everything in sync, the remote-tracking branches, what you added)."""
    t = Task(5, "Wrap up", 10, ctx.repo_mode)
    f = ctx.facts
    s51 = ctx.step("5.1")
    st = parse_status(s51)
    t.check(2, "5.1 status: On branch main, up to date with 'origin/main', working tree clean",
            lambda: "On branch main" in s51 and st.up_to_date and "'origin/main'" in s51 and st.clean)
    names = set(branch_names(ctx.step("5.2")))
    t.check(2, "5.2 branch -r lists origin/main, origin/feature/turn-calibration and upstream/main",
            lambda: {"origin/main", f"origin/{FEATURE_BRANCH}", "upstream/main"} <= names)
    s53 = ctx.step("5.3")
    entries = oneline_entries(s53)
    t.check(2, "5.3 log upstream/main..main lists exactly your three new commits (newest first: your docs commit, "
               "the field team note, the team contact line)",
            lambda: [strip_decoration(e.subject) for e in entries] == [LOCAL_SUBJECT, WEB2_SUBJECT, WEB1_SUBJECT])
    t.check(1, "ANSWER-3 is 3 (commits main has that the course repository does not)",
            lambda: get_answer_int(ctx.text, 3) == "3")
    t.check(1, "live repo: main is the same commit as origin/main, the working tree is clean and no merge or rebase is in progress",
            lambda: f.commits_above_base() > 0 and f.rev("refs/remotes/origin/main") == f.main_tip()
            and f.working_tree_clean(), needs_repo=True)
    t.check(1, "live repo: main is exactly 3 commits above the course's last commit",
            lambda: f.commits_above_base() == 3, needs_repo=True)
    added = f.added() if ctx.repo_mode else []
    t.check(1, "live repo: the commit numbers pasted in 5.3 are those three commits",
            lambda: len(entries) == 3 and len(added) == 3
            and all(sha_matches(e.sha, a.sha) for e, a in zip(entries, reversed(added))), needs_repo=True)
    return t

"""Detects pasted output that does not belong to the repository being graded."""
from __future__ import annotations

import re
from typing import List, Set

from .context import Ctx
from .facts import slug_of
from .tasks import pasted_origin_slug
from .textutil import line_shas

BRACKET_SHA_RE = re.compile(r"\[[^\]]*? ([0-9a-f]{7,40})\]")
RANGE_SHA_RE = re.compile(r"(?m)^\s+([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s")
UPDATING_SHA_RE = re.compile(r"(?m)^Updating ([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})\s*$")
TO_LINE_RE = re.compile(r"(?m)^To (\S+)\s*$")


def integrity_warnings(ctx: Ctx) -> List[str]:
    """Return human-readable warnings; an empty list means the pasted text matches this repo."""
    if not ctx.repo_mode:
        return []
    facts = ctx.facts
    warnings: List[str] = []
    live_slug = slug_of(facts.remote_url("origin"))
    pasted_slug = pasted_origin_slug(ctx)
    if live_slug and pasted_slug and live_slug != pasted_slug:
        warnings.append(f"the pasted 'git remote -v' shows origin as {pasted_slug} but this clone's origin is {live_slug}")
    wrong_target: Set[str] = set()
    foreign: Set[str] = set()
    for text in ctx.steps.values():
        for match in TO_LINE_RE.finditer(text):
            target = slug_of(match.group(1))
            if target and live_slug and target != live_slug:
                wrong_target.add(target)
        tokens = line_shas(text) + BRACKET_SHA_RE.findall(text)
        for pair in RANGE_SHA_RE.findall(text) + UPDATING_SHA_RE.findall(text):
            tokens += list(pair)
        for token in tokens:
            if not facts.commit_exists(token):
                foreign.add(token)
    if wrong_target:
        warnings.append("a pasted push or fetch names another repository than this clone's origin: "
                        + ", ".join(sorted(wrong_target)))
    if foreign:
        shown = ", ".join(sorted(foreign)[:6])
        warnings.append(f"{len(foreign)} commit SHA(s) in the pasted text do not exist in this repository "
                        f"(e.g. {shown}); the outputs were not produced in this clone")
    return warnings

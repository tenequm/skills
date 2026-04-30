#!/usr/bin/env python3

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
MAX_SKILL_LINES = 500
STANDARD_FIELDS = {
    "allowed-tools",
    "compatibility",
    "description",
    "license",
    "metadata",
    "name",
}
OPENCLAW_EXTENSION_FIELDS = {
    "command-arg-mode",
    "command-dispatch",
    "command-tool",
    "disable-model-invocation",
    "homepage",
    "user-invocable",
}
# ClawHub allows these `metadata.*` keys to be nested mappings (per
# docs/skill-format.md). Other metadata values must remain strings to satisfy
# Anthropic's `metadata: dict[str, str]` contract.
CLAWHUB_NESTED_METADATA_KEYS = {"openclaw", "clawdbot", "clawdis"}


@dataclass
class LintIssue:
    path: Path
    message: str


@dataclass
class LintResult:
    errors: list[LintIssue]
    warnings: list[LintIssue]


def read_frontmatter(skill_md: Path) -> tuple[dict[str, Any] | None, str | None]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, None

    frontmatter_text = match.group(1)
    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML frontmatter: {exc}") from exc

    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must parse to a mapping.")

    body = text[match.end() :].strip()
    return parsed, body


def expect_string(value: Any, field: str, issues: list[LintIssue], path: Path) -> str | None:
    if not isinstance(value, str):
        issues.append(LintIssue(path, f"`{field}` must be a string."))
        return None
    return value


def lint_skill(skill_md: Path) -> LintResult:
    issues: list[LintIssue] = []
    warnings: list[LintIssue] = []
    try:
        frontmatter, body = read_frontmatter(skill_md)
    except ValueError as exc:
        return LintResult(errors=[LintIssue(skill_md, str(exc))], warnings=[])

    if frontmatter is None:
        return LintResult(
            errors=[LintIssue(skill_md, "missing YAML frontmatter at top of file.")], warnings=[]
        )

    skill_dir = skill_md.parent.name
    license_file = skill_md.parent / "LICENSE.txt"

    if not license_file.exists():
        issues.append(
            LintIssue(skill_md, "missing required `LICENSE.txt` file in skill directory.")
        )
    elif license_file.stat().st_size == 0:
        issues.append(LintIssue(skill_md, "`LICENSE.txt` must not be empty."))

    name = frontmatter.get("name")
    if name is None:
        issues.append(LintIssue(skill_md, "missing required `name` field."))
    else:
        name_str = expect_string(name, "name", issues, skill_md)
        if name_str is not None:
            if len(name_str) > MAX_NAME_LENGTH:
                issues.append(LintIssue(skill_md, f"`name` exceeds {MAX_NAME_LENGTH} characters."))
            if not NAME_RE.fullmatch(name_str):
                issues.append(
                    LintIssue(
                        skill_md,
                        "`name` must match `^[a-z0-9]+(?:-[a-z0-9]+)*$` and not start/end with a hyphen.",
                    )
                )
            if name_str != skill_dir:
                issues.append(
                    LintIssue(
                        skill_md, f"`name` must match the parent directory name `{skill_dir}`."
                    )
                )

    description = frontmatter.get("description")
    if description is None:
        issues.append(LintIssue(skill_md, "missing required `description` field."))
    else:
        description_str = expect_string(description, "description", issues, skill_md)
        if description_str is not None:
            description_len = len(description_str.strip())
            if description_len == 0:
                issues.append(LintIssue(skill_md, "`description` must be non-empty."))
            if description_len > MAX_DESCRIPTION_LENGTH:
                issues.append(
                    LintIssue(
                        skill_md, f"`description` exceeds {MAX_DESCRIPTION_LENGTH} characters."
                    )
                )

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        compatibility_str = expect_string(compatibility, "compatibility", issues, skill_md)
        if compatibility_str is not None:
            compatibility_len = len(compatibility_str.strip())
            if compatibility_len == 0 or compatibility_len > MAX_COMPATIBILITY_LENGTH:
                issues.append(
                    LintIssue(
                        skill_md,
                        f"`compatibility` must be between 1 and {MAX_COMPATIBILITY_LENGTH} characters.",
                    )
                )

    metadata = frontmatter.get("metadata")
    if metadata is None:
        issues.append(LintIssue(skill_md, "missing required repo policy field `metadata.version`."))
    elif not isinstance(metadata, dict):
        issues.append(LintIssue(skill_md, "`metadata` must be a mapping."))
    else:
        for key, value in metadata.items():
            if not isinstance(key, str):
                issues.append(LintIssue(skill_md, "`metadata` keys must be strings."))
                break
            if key in CLAWHUB_NESTED_METADATA_KEYS:
                if not isinstance(value, dict):
                    issues.append(LintIssue(skill_md, f"`metadata.{key}` must be a mapping."))
            elif not isinstance(value, str):
                issues.append(LintIssue(skill_md, f"`metadata.{key}` must be a string."))
        version = metadata.get("version")
        if version is None:
            issues.append(
                LintIssue(skill_md, "missing required repo policy field `metadata.version`.")
            )
        elif not isinstance(version, str) or not version.strip():
            issues.append(LintIssue(skill_md, "`metadata.version` must be a non-empty string."))

    allowed_fields = STANDARD_FIELDS | OPENCLAW_EXTENSION_FIELDS
    unknown_fields = sorted(set(frontmatter) - allowed_fields)
    if unknown_fields:
        issues.append(
            LintIssue(
                skill_md,
                "unexpected top-level frontmatter fields: "
                + ", ".join(f"`{field}`" for field in unknown_fields),
            )
        )

    if body is None or not body:
        issues.append(LintIssue(skill_md, "skill body must not be empty."))

    line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
    if line_count > MAX_SKILL_LINES:
        warnings.append(
            LintIssue(
                skill_md, f"SKILL.md exceeds the repo policy limit of {MAX_SKILL_LINES} lines."
            )
        )

    return LintResult(errors=issues, warnings=warnings)


def lint_skills(repo_root: Path) -> int:
    print("==> Repository skill policy lint")
    skill_files = sorted((repo_root / "skills").glob("*/SKILL.md"))

    issues: list[LintIssue] = []
    warnings: list[LintIssue] = []
    for skill_md in skill_files:
        result = lint_skill(skill_md)
        issues.extend(result.errors)
        warnings.extend(result.warnings)

    if issues:
        for issue in issues:
            print(f"{issue.path.as_posix()}: {issue.message}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"warning: {warning.path.as_posix()}: {warning.message}", file=sys.stderr)

    print(f"Validated {len(skill_files)} skills.")
    return 0


def normalize_skill(skill_dir: Path, dest_root: Path) -> Path:
    dest_dir = dest_root / skill_dir.name
    dest_dir.mkdir(parents=True, exist_ok=True)
    for source in skill_dir.rglob("*"):
        target = dest_dir / source.relative_to(skill_dir)
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if source.name != "SKILL.md":
            target.write_bytes(source.read_bytes())
            continue

        text = source.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            target.write_text(text, encoding="utf-8")
            continue

        kept_lines: list[str] = []
        for line in match.group(1).splitlines():
            if not line.startswith(" ") and ":" in line:
                key = line.split(":", 1)[0].strip()
                if key in OPENCLAW_EXTENSION_FIELDS:
                    continue
            kept_lines.append(line)

        normalized = "---\n" + "\n".join(kept_lines) + "\n---\n" + text[match.end() :]
        target.write_text(normalized, encoding="utf-8")

    return dest_dir


def validate_skills_ref(repo_root: Path) -> int:
    print("==> Agent Skills reference validation")
    skill_dirs = sorted(
        path
        for path in (repo_root / "skills").glob("*")
        if path.is_dir() and (path / "SKILL.md").exists()
    )
    failed = False

    with tempfile.TemporaryDirectory(prefix="skills-ref-") as temp_dir:
        temp_root = Path(temp_dir)
        for skill_dir in skill_dirs:
            normalized_dir = normalize_skill(skill_dir, temp_root)
            result = subprocess.run(
                ["uvx", "--from", "skills-ref", "agentskills", "validate", str(normalized_dir)],
                cwd=repo_root,
                text=True,
            )
            if result.returncode != 0:
                failed = True

    return 1 if failed else 0


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    code = lint_skills(repo_root)
    if code != 0:
        return code

    code = validate_skills_ref(repo_root)
    if code != 0:
        return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

import yaml
from generate_readme import clawhub_slug

EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # pragma: allowlist secret


@dataclass
class FileChange:
    description: str


@dataclass
class SkillRelease:
    slug: str
    state: str
    path: str
    current_version: str | None
    previous_version: str | None
    display_name: str | None
    changelog: str
    file_changes: list[str] = field(default_factory=list)
    bundle_path: str | None = None

    def to_manifest(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "state": self.state,
            "path": self.path,
            "display_name": self.display_name or self.slug,
            "current_version": self.current_version,
            "previous_version": self.previous_version,
            "changelog": self.changelog,
            "file_changes": self.file_changes,
            "bundle_path": self.bundle_path,
        }


def run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=check,
        capture_output=True,
        text=True,
    )


def git_output(repo_root: Path, *args: str) -> str:
    return run_git(repo_root, *args).stdout.strip()


def valid_commit(repo_root: Path, sha: str) -> bool:
    if not sha or set(sha) == {"0"}:
        return False
    result = run_git(repo_root, "cat-file", "-e", f"{sha}^{{commit}}", check=False)
    return result.returncode == 0


def normalize_before(repo_root: Path, before: str) -> str:
    return resolve_commit(repo_root, before) if valid_commit(repo_root, before) else EMPTY_TREE_SHA


def resolve_commit(repo_root: Path, ref: str) -> str:
    result = run_git(repo_root, "rev-parse", "--verify", ref, check=False)
    if result.returncode != 0:
        raise SystemExit(f"error: could not resolve git ref {ref!r}")
    return result.stdout.strip()


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1)) or {}
    if not isinstance(parsed, dict):
        return {}

    values: dict[str, str] = {}
    name = parsed.get("name")
    if isinstance(name, str):
        values["name"] = name.strip()

    metadata = parsed.get("metadata")
    if isinstance(metadata, dict):
        version = metadata.get("version")
        if isinstance(version, str):
            values["version"] = version.strip()

    return values


def parse_heading(text: str) -> str | None:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def git_show(repo_root: Path, ref: str, relative_path: str) -> str | None:
    result = run_git(repo_root, "show", f"{ref}:{relative_path}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def path_for_output(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def skill_from_path(path: str) -> tuple[str, str] | None:
    parts = PurePosixPath(path).parts
    if len(parts) < 2 or parts[0] != "skills":
        return None
    skill = parts[1]
    rel_path = PurePosixPath(*parts[2:]).as_posix() if len(parts) > 2 else ""
    return skill, rel_path


def describe_file_change(
    status: str, old_path: str | None, new_path: str | None, skill: str
) -> str:
    if status == "R":
        assert old_path is not None and new_path is not None
        old_skill = skill_from_path(old_path)
        new_skill = skill_from_path(new_path)
        if old_skill and old_skill[0] == skill and new_skill and new_skill[0] == skill:
            return f"renamed `{old_skill[1]}` -> `{new_skill[1]}`"
        if old_skill and old_skill[0] == skill:
            return f"moved out `{old_skill[1]}` -> `{new_path}`"
        assert new_skill is not None
        return f"moved in `{old_path}` -> `{new_skill[1]}`"

    path = new_path or old_path
    assert path is not None
    path_info = skill_from_path(path)
    rel_path = path_info[1] if path_info else path

    labels = {
        "A": "added",
        "M": "modified",
        "D": "deleted",
        "C": "copied",
        "T": "type-changed",
    }
    return f"{labels.get(status, status.lower())} `{rel_path}`"


def collect_changed_skills(repo_root: Path, before: str, after: str) -> dict[str, list[str]]:
    diff_output = git_output(
        repo_root, "diff", "--name-status", "--find-renames", before, after, "--", "skills"
    )
    changes: dict[str, list[str]] = {}
    if not diff_output:
        return changes

    for line in diff_output.splitlines():
        parts = line.split("\t")
        status = parts[0][0]
        if status == "R":
            _, old_path, new_path = parts
            for candidate in (old_path, new_path):
                skill_info = skill_from_path(candidate)
                if not skill_info:
                    continue
                skill, _ = skill_info
                changes.setdefault(skill, []).append(
                    describe_file_change(status, old_path, new_path, skill)
                )
            continue

        _, path = parts
        skill_info = skill_from_path(path)
        if not skill_info:
            continue
        skill, _ = skill_info
        changes.setdefault(skill, []).append(
            describe_file_change(status, path if status == "D" else None, path, skill)
        )

    for skill in list(changes):
        deduped = []
        seen = set()
        for change in changes[skill]:
            if change in seen:
                continue
            seen.add(change)
            deduped.append(change)
        changes[skill] = deduped

    return changes


def collect_all_skills(repo_root: Path) -> dict[str, list[str]]:
    return {
        skill_dir.name: ["bootstrap publish of current skill contents"]
        for skill_dir in sorted((repo_root / "skills").glob("*"))
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists()
    }


def bundle_skill(skill_dir: Path, bundle_path: Path) -> None:
    if bundle_path.exists():
        bundle_path.unlink()
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_dir() or path.name == ".DS_Store":
                continue
            archive.write(
                path, arcname=(skill_dir.name + "/" + path.relative_to(skill_dir).as_posix())
            )


def build_changelog(skill: SkillRelease) -> str:
    summary = []
    if skill.state == "added":
        summary.append(f"Initial publish of {skill.slug} {skill.current_version}.")
    elif skill.state == "modified":
        summary.append(
            f"Updated {skill.slug} from {skill.previous_version} to {skill.current_version}."
        )
    elif skill.state == "deleted":
        summary.append(f"Removed {skill.slug} from the repository.")

    if skill.file_changes:
        summary.append("Changes:")
        summary.extend(f"- {change}" for change in skill.file_changes[:12])

    return "\n".join(summary)


def build_release(
    repo_root: Path,
    before: str,
    after: str,
    dist_dir: Path,
    release_all: bool = False,
) -> tuple[list[SkillRelease], list[str]]:
    changed_skills = (
        collect_all_skills(repo_root)
        if release_all
        else collect_changed_skills(repo_root, before, after)
    )
    releases: list[SkillRelease] = []
    errors: list[str] = []

    for slug in sorted(changed_skills):
        skill_dir = repo_root / "skills" / slug
        current_skill_md = skill_dir / "SKILL.md"
        previous_skill_text = (
            None if release_all else git_show(repo_root, before, f"skills/{slug}/SKILL.md")
        )
        current_skill_text = read_text(current_skill_md) if current_skill_md.exists() else None

        state = "deleted"
        if current_skill_md.exists() and previous_skill_text is None:
            state = "added"
        elif current_skill_md.exists():
            state = "modified"

        current_meta = parse_frontmatter(current_skill_text or "")
        previous_meta = parse_frontmatter(previous_skill_text or "")

        current_version = current_meta.get("version")
        previous_version = previous_meta.get("version")
        display_name = parse_heading(current_skill_text or "") or current_meta.get("name") or slug

        release = SkillRelease(
            slug=clawhub_slug(slug),
            state=state,
            path=f"skills/{slug}",
            current_version=current_version,
            previous_version=previous_version,
            display_name=display_name,
            changelog="",
            file_changes=changed_skills[slug],
        )

        if state != "deleted":
            if not current_version:
                errors.append(f"{slug}: missing version in SKILL.md frontmatter.")
            elif not release_all and state == "modified" and current_version == previous_version:
                errors.append(
                    f"{slug}: changed files detected but version did not change (still {current_version})."
                )

            if current_version:
                bundle_name = f"{slug}-{current_version}.zip"
                bundle_path = dist_dir / "bundles" / bundle_name
                bundle_skill(skill_dir, bundle_path)
                release.bundle_path = path_for_output(repo_root, bundle_path)

        release.changelog = build_changelog(release)
        releases.append(release)

    return releases, errors


def release_notes(
    before: str, after: str, releases: Iterable[SkillRelease], generated_at: datetime
) -> str:
    release_list = list(releases)
    published = [release for release in release_list if release.state != "deleted"]
    deleted = [release for release in release_list if release.state == "deleted"]

    lines = [
        f"# Skills Release `{after[:7]}`",
        "",
        f"- Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- Compare: `{before[:7]}` -> `{after[:7]}`",
        "",
    ]

    if published:
        lines.append("## Published Skills")
        for release in published:
            version_line = f"`{release.slug}` {release.current_version}"
            if release.previous_version:
                version_line += f" (was {release.previous_version})"
            lines.append(f"- {version_line}")
            lines.extend(f"  - {change}" for change in release.file_changes)
        lines.append("")

    if deleted:
        lines.append("## Removed Skills")
        for release in deleted:
            lines.append(f"- `{release.slug}`")
            lines.extend(f"  - {change}" for change in release.file_changes)
        lines.append("")

    if not published and not deleted:
        lines.append("No skill changes detected.")
        lines.append("")

    lines.append("## Notes")
    lines.append(
        "- Attached zip assets are raw skill bundles for manual install or external installers."
    )
    lines.append(
        "- Claude Desktop `.mcpb` packages are for MCP desktop extensions, not for raw skill folders."
    )
    lines.append("")

    return "\n".join(lines)


def write_github_output(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a skill-aware GitHub release.")
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument(
        "--all", action="store_true", help="Prepare a bootstrap release for all current skills."
    )
    parser.add_argument("--dist-dir", required=True)
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--notes-path", required=True)
    parser.add_argument("--github-output")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    dist_dir = repo_root / args.dist_dir
    manifest_path = repo_root / args.manifest_path
    notes_path = repo_root / args.notes_path

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        before = EMPTY_TREE_SHA
        after = resolve_commit(repo_root, args.after or "HEAD")
    else:
        if not args.before or not args.after:
            raise SystemExit("error: `--before` and `--after` are required unless `--all` is set.")
        before = normalize_before(repo_root, args.before)
        after = resolve_commit(repo_root, args.after)

    releases, errors = build_release(repo_root, before, after, dist_dir, release_all=args.all)

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    generated_at = datetime.now(UTC)
    tag = f"skills-{after[:7]}"
    title = f"Skills release {after[:7]}"

    manifest = {
        "release": {
            "tag": tag,
            "title": title,
            "before": before,
            "after": after,
            "generated_at": generated_at.isoformat(),
        },
        "skills": [release.to_manifest() for release in releases],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(release_notes(before, after, releases, generated_at), encoding="utf-8")

    if args.github_output:
        published_count = sum(1 for release in releases if release.state != "deleted")
        outputs = {
            "changed": "true" if releases else "false",
            "published_count": str(published_count),
            "publishable": "true" if published_count > 0 else "false",
            "tag": tag,
            "title": title,
            "notes_path": path_for_output(repo_root, notes_path),
            "manifest_path": path_for_output(repo_root, manifest_path),
            "asset_glob": path_for_output(repo_root, dist_dir / "bundles" / "*.zip"),
        }
        write_github_output(Path(args.github_output), outputs)

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

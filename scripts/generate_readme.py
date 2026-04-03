#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

README_START = "<!-- GENERATED_SKILLS_TABLE_START -->"
README_END = "<!-- GENERATED_SKILLS_TABLE_END -->"
DEFAULT_REPO = "tenequm/skills"
DEFAULT_LATEST_TAG = "skills-latest"
DEFAULT_CLAWHUB_BASE = "https://clawhub.ai/skills"

CLAWHUB_SLUG_OVERRIDES: dict[str, str] = {
    "erc-8004": "erc-8004-development",
    "founder-playbook": "founder-playbook-web3",
    "openclaw-ref": "openclaw-reference",
    "polish": "code-polish",
    "skill-factory": "claude-skill-factory",
    "skill-finder": "claude-skill-finder",
    "vite": "vite-react",
    "x402": "x402-development",
}


def clawhub_slug(folder_name: str) -> str:
    return CLAWHUB_SLUG_OVERRIDES.get(folder_name, folder_name)


@dataclass
class SkillInfo:
    slug: str
    description: str
    version: str | None
    clawhub_slug: str = ""


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

    description = parsed.get("description")
    if isinstance(description, str):
        values["description"] = re.sub(r"\s+", " ", description).strip()

    metadata = parsed.get("metadata")
    if isinstance(metadata, dict):
        version = metadata.get("version")
        if isinstance(version, str):
            values["version"] = version.strip()

    return values


def collect_skills(repo_root: Path) -> list[SkillInfo]:
    skills: list[SkillInfo] = []
    for skill_md in sorted((repo_root / "skills").glob("*/SKILL.md")):
        slug = skill_md.parent.name
        meta = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        description = meta.get("description", "").replace("|", "\\|")
        skills.append(
            SkillInfo(
                slug=slug,
                description=description,
                version=meta.get("version"),
                clawhub_slug=clawhub_slug(slug),
            )
        )
    return skills


def build_table(skills: list[SkillInfo], repo: str, latest_tag: str, clawhub_base: str) -> str:
    lines = [
        README_START,
        "| Skill | Version | Bundle | ClawHub | Description |",
        "|-------|---------|--------|---------|-------------|",
    ]

    for skill in skills:
        bundle_url = f"https://github.com/{repo}/releases/download/{latest_tag}/{skill.slug}.zip"
        clawhub_url = f"{clawhub_base}/{skill.clawhub_slug}"
        lines.append(
            "| "
            f"`{skill.slug}` | "
            f"{skill.version or '-'} | "
            f"[zip]({bundle_url}) | "
            f"[page]({clawhub_url}) | "
            f"{skill.description or '-'} |"
        )

    lines.append(README_END)
    return "\n".join(lines)


def update_readme(readme_path: Path, table: str) -> None:
    content = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(README_START)}.*?{re.escape(README_END)}",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise SystemExit("error: README is missing generated table markers.")
    updated = pattern.sub(table, content)
    readme_path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the skills table in README.md.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--latest-tag", default=DEFAULT_LATEST_TAG)
    parser.add_argument("--clawhub-base", default=DEFAULT_CLAWHUB_BASE)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    readme_path = repo_root / "README.md"
    skills = collect_skills(repo_root)
    table = build_table(skills, args.repo, args.latest_tag, args.clawhub_base)

    current = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(README_START)}.*?{re.escape(README_END)}",
        re.DOTALL,
    )
    if not pattern.search(current):
        raise SystemExit("error: README is missing generated table markers.")

    updated = pattern.sub(table, current)
    if args.check:
        if updated != current:
            raise SystemExit(
                "error: README.md is out of date. Run `uv run python scripts/generate_readme.py`."
            )
        return 0

    update_readme(readme_path, table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

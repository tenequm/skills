#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from generate_readme import collect_skills


def run(
    command: list[str], repo_root: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo_root,
        check=check,
        text=True,
        capture_output=True,
    )


def bundle_skill(skill_dir: Path, bundle_path: Path) -> None:
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_path.exists():
        bundle_path.unlink()
    with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_dir() or path.name == ".DS_Store":
                continue
            archive.write(
                path, arcname=(skill_dir.name + "/" + path.relative_to(skill_dir).as_posix())
            )


def classify_clawhub_error(message: str) -> tuple[str, bool]:
    if "Rate limit: max 5 new skills per hour" in message:
        return ("rate_limited", True)
    if "Slug is already taken" in message:
        return ("slug_taken", False)
    if "slug is locked to a deleted or banned account" in message.lower():
        return ("slug_locked", False)
    return ("unknown", False)


def publish_clawhub(args: argparse.Namespace, repo_root: Path) -> int:
    manifest_path = repo_root / args.manifest
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    skills = [skill for skill in manifest.get("skills", []) if skill.get("state") != "deleted"]
    if not skills:
        print("No published skills in manifest.")
        return 0

    failures: list[dict[str, object]] = []
    successes: list[dict[str, str]] = []
    for skill in skills:
        command = [
            "clawhub",
            "--no-input",
            "publish",
            skill["path"],
            "--slug",
            skill["slug"],
            "--name",
            skill["display_name"],
            "--version",
            skill["current_version"],
            "--changelog",
            skill["changelog"],
            "--tags",
            "latest",
        ]
        print("Publishing", skill["slug"], skill["current_version"], flush=True)
        try:
            run(command, repo_root)
        except subprocess.CalledProcessError as exc:
            error = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            category, retryable = classify_clawhub_error(error)
            failures.append(
                {
                    "slug": skill["slug"],
                    "version": skill["current_version"],
                    "category": category,
                    "retryable": retryable,
                    "error": error,
                }
            )
        else:
            successes.append(
                {
                    "slug": skill["slug"],
                    "version": skill["current_version"],
                }
            )

    if args.results_path:
        results_path = repo_root / args.results_path
        results_path.parent.mkdir(parents=True, exist_ok=True)
        results_path.write_text(
            json.dumps(
                {
                    "manifest": args.manifest,
                    "successful": successes,
                    "failed": failures,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    if failures:
        retryable_slugs = {failure["slug"] for failure in failures if failure["retryable"]}
        if args.failures_manifest:
            failures_manifest_path = repo_root / args.failures_manifest
            failures_manifest_path.parent.mkdir(parents=True, exist_ok=True)
            failed_manifest = {
                "release": manifest.get("release"),
                "skills": [skill for skill in skills if skill["slug"] in retryable_slugs],
            }
            failures_manifest_path.write_text(
                json.dumps(failed_manifest, indent=2) + "\n",
                encoding="utf-8",
            )
        print("\nClawHub publish failures:", file=sys.stderr)
        for failure in failures:
            print(
                f"- {failure['slug']} [{failure['category']}]: {failure['error']}",
                file=sys.stderr,
            )
        if args.results_path:
            print(f"\nSaved publish results to {args.results_path}", file=sys.stderr)
        if args.failures_manifest:
            print(
                f"Saved retryable-failures manifest to {args.failures_manifest}",
                file=sys.stderr,
            )
        return 1

    if args.results_path:
        print(f"Saved publish results to {args.results_path}")
    return 0


def publish_latest_bundles(args: argparse.Namespace, repo_root: Path) -> int:
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    skills = collect_skills(repo_root)
    bundle_paths: list[Path] = []
    for skill in skills:
        bundle_path = output_dir / f"{skill.slug}.zip"
        bundle_skill(repo_root / "skills" / skill.slug, bundle_path)
        bundle_paths.append(bundle_path)

    notes_path = output_dir / "notes.md"
    index_path = output_dir / "catalog.json"
    notes_path.write_text(
        "\n".join(
            [
                "# Latest skill bundles",
                "",
                "Stable download assets for the current state of the repository.",
                "",
                f"- Skills bundled: {len(skills)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    index_path.write_text(
        json.dumps(
            {
                "tag": args.tag,
                "skills": [
                    {
                        "slug": skill.slug,
                        "version": skill.version,
                        "bundle": f"{skill.slug}.zip",
                    }
                    for skill in skills
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    view = run(["gh", "release", "view", args.tag, "--json", "assets"], repo_root, check=False)
    if view.returncode != 0:
        run(
            [
                "gh",
                "release",
                "create",
                args.tag,
                "--title",
                args.title,
                "--notes-file",
                str(notes_path),
            ],
            repo_root,
        )
    else:
        run(
            [
                "gh",
                "release",
                "edit",
                args.tag,
                "--title",
                args.title,
                "--notes-file",
                str(notes_path),
            ],
            repo_root,
        )
        assets = json.loads(view.stdout).get("assets", [])
        for asset in assets:
            run(["gh", "release", "delete-asset", args.tag, asset["name"], "--yes"], repo_root)

    run(
        [
            "gh",
            "release",
            "upload",
            args.tag,
            str(index_path),
            str(notes_path),
            *[str(path) for path in bundle_paths],
        ],
        repo_root,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish release artifacts for this skills repository."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    clawhub = subparsers.add_parser(
        "clawhub", help="Publish changed skills from a manifest to ClawHub."
    )
    clawhub.add_argument("--manifest", required=True)
    clawhub.add_argument("--results-path", default="dist/releases/clawhub-publish-results.json")
    clawhub.add_argument(
        "--failures-manifest",
        default="dist/releases/clawhub-retry-manifest.json",
    )
    clawhub.set_defaults(handler=publish_clawhub)

    latest = subparsers.add_parser(
        "latest-bundles", help="Publish the rolling latest bundle GitHub release."
    )
    latest.add_argument("--tag", default="skills-latest")
    latest.add_argument("--title", default="Latest skill bundles")
    latest.add_argument("--output-dir", default="dist/latest-bundles")
    latest.set_defaults(handler=publish_latest_bundles)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    return args.handler(args, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())

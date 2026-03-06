# Gh-Cli - Releases

**Pages:** 9

---

## gh release delete

**URL:** https://cli.github.com/manual/gh_release_delete

**Contents:**
- gh release delete
  - Options
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh release delete <tag> [flags]
```

---

## gh release upload

**URL:** https://cli.github.com/manual/gh_release_upload

**Contents:**
- gh release upload
  - Options
  - Options inherited from parent commands
  - See also

Upload asset files to a GitHub Release.

To define a display label for an asset, append text starting with # after the file name.

**Examples:**

Example 1 (unknown):
```unknown
gh release upload <tag> <files>... [flags]
```

---

## gh release delete-asset

**URL:** https://cli.github.com/manual/gh_release_delete-asset

**Contents:**
- gh release delete-asset
  - Options
  - Options inherited from parent commands
  - See also

Delete an asset from a release

**Examples:**

Example 1 (unknown):
```unknown
gh release delete-asset <tag> <asset-name> [flags]
```

---

## gh release view

**URL:** https://cli.github.com/manual/gh_release_view

**Contents:**
- gh release view
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also

View information about a GitHub Release.

Without an explicit tag name argument, the latest release in the project is shown.

apiUrl, assets, author, body, createdAt, databaseId, id, isDraft, isImmutable, isPrerelease, name, publishedAt, tagName, tarballUrl, targetCommitish, uploadUrl, url, zipballUrl

**Examples:**

Example 1 (unknown):
```unknown
gh release view [<tag>] [flags]
```

---

## gh release verify-asset

**URL:** https://cli.github.com/manual/gh_release_verify-asset

**Contents:**
- gh release verify-asset
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Verify that a given asset file originated from a specific GitHub Release using cryptographically signed attestations.

An attestation is a claim made by GitHub regarding a release and its assets.

**Examples:**

Example 1 (unknown):
```unknown
gh release verify-asset [<tag>] <file-path> [flags]
```

Example 2 (unknown):
```unknown
This command checks that the asset you provide matches a valid attestation for the specified release (or the latest release, if no tag is given). It ensures the asset's integrity by validating that the asset's digest matches the subject in the attestation and that the attestation is associated with the release.
```

Example 3 (bash):
```bash
# Verify an asset from the latest release
$ gh release verify-asset ./dist/my-asset.zip

# Verify an asset from a specific release tag
$ gh release verify-asset v1.2.3 ./dist/my-asset.zip

# Verify an asset from a specific release tag and output the attestation in JSON format
$ gh release verify-asset v1.2.3 ./dist/my-asset.zip --format json
```

---

## gh release download

**URL:** https://cli.github.com/manual/gh_release_download

**Contents:**
- gh release download
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Download assets from a GitHub release.

Without an explicit tag name argument, assets are downloaded from the latest release in the project. In this case, --pattern or --archive is required.

**Examples:**

Example 1 (unknown):
```unknown
gh release download [<tag>] [flags]
```

Example 2 (bash):
```bash
# Download all assets from a specific release
$ gh release download v1.2.3

# Download only Debian packages for the latest release
$ gh release download --pattern '*.deb'

# Specify multiple file patterns
$ gh release download -p '*.deb' -p '*.rpm'

# Download the archive of the source code for a release
$ gh release download v1.2.3 --archive=zip
```

---

## gh release edit

**URL:** https://cli.github.com/manual/gh_release_edit

**Contents:**
- gh release edit
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh release edit <tag>
```

Example 2 (bash):
```bash
# Publish a release that was previously a draft
$ gh release edit v1.0 --draft=false

# Update the release notes from the content of a file
$ gh release edit v1.0 --notes-file /path/to/release_notes.md
```

---

## gh release verify

**URL:** https://cli.github.com/manual/gh_release_verify

**Contents:**
- gh release verify
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Verify that a GitHub Release is accompanied by a valid cryptographically signed attestation.

An attestation is a claim made by GitHub regarding a release and its assets.

This command checks that the specified release (or the latest release, if no tag is given) has a valid attestation. It fetches the attestation for the release and prints metadata about all assets referenced in the attestation, including their digests.

**Examples:**

Example 1 (unknown):
```unknown
gh release verify [<tag>] [flags]
```

Example 2 (bash):
```bash
# Verify the latest release
gh release verify

# Verify a specific release by tag
gh release verify v1.2.3

# Verify a specific release by tag and output the attestation in JSON format
gh release verify v1.2.3 --format json
```

---

## gh release

**URL:** https://cli.github.com/manual/gh_release

**Contents:**
- gh release
  - General commands
  - Targeted commands
  - Options
  - See also

---

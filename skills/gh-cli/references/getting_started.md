# Gh-Cli - Getting Started

**Pages:** 1

---

## gh auth setup-git

**URL:** https://cli.github.com/manual/gh_auth_setup-git

**Contents:**
- gh auth setup-git
  - Options
  - Examples
  - See also

This command configures git to use GitHub CLI as a credential helper. For more information on git credential helpers please reference: https://git-scm.com/docs/gitcredentials.

By default, GitHub CLI will be set as the credential helper for all authenticated hosts. If there is no authenticated hosts the command fails with an error.

Alternatively, use the --hostname flag to specify a single host to be configured. If the host is not authenticated with, the command fails with an error.

**Examples:**

Example 1 (unknown):
```unknown
gh auth setup-git [flags]
```

Example 2 (bash):
```bash
# Configure git to use GitHub CLI as the credential helper for all authenticated hosts
$ gh auth setup-git

# Configure git to use GitHub CLI as the credential helper for enterprise.internal host
$ gh auth setup-git --hostname enterprise.internal
```

---

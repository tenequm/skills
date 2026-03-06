# Gh-Cli - Repositories

**Pages:** 72

---

## gh repo autolink

**URL:** https://cli.github.com/manual/gh_repo_autolink

**Contents:**
- gh repo autolink
  - Available commands
  - Options
  - See also

Autolinks link issues, pull requests, commit messages, and release descriptions to external third-party services.

Autolinks require admin role to view or manage.

For more information, see https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/configuring-autolinks-to-reference-external-resources

---

## gh repo gitignore list

**URL:** https://cli.github.com/manual/gh_repo_gitignore_list

**Contents:**
- gh repo gitignore list
  - ALIASES
  - See also

List available repository gitignore templates

**Examples:**

Example 1 (unknown):
```unknown
gh repo gitignore list
```

---

## gh label list

**URL:** https://cli.github.com/manual/gh_label_list

**Contents:**
- gh label list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - Examples
  - See also

Display labels in a GitHub repository.

When using the --search flag results are sorted by best match of the query. This behavior cannot be configured with the --order or --sort flags.

color, createdAt, description, id, isDefault, name, updatedAt, url

**Examples:**

Example 1 (unknown):
```unknown
gh label list [flags]
```

Example 2 (bash):
```bash
# Sort labels by name
$ gh label list --sort name

# Find labels with "bug" in the name or description
$ gh label list --search bug
```

---

## gh repo rename

**URL:** https://cli.github.com/manual/gh_repo_rename

**Contents:**
- gh repo rename
  - Options
  - Examples
  - See also

Rename a GitHub repository.

<new-name> is the desired repository name without the owner.

By default, the current repository is renamed. Otherwise, the repository specified with --repo is renamed.

To transfer repository ownership to another user account or organization, you must follow additional steps on github.com.

For more information on transferring repository ownership, see: https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository

**Examples:**

Example 1 (unknown):
```unknown
gh repo rename [<new-name>] [flags]
```

Example 2 (bash):
```bash
# Rename the current repository (foo/bar -> foo/baz)
$ gh repo rename baz

# Rename the specified repository (qux/quux -> qux/baz)
$ gh repo rename -R qux/quux baz
```

---

## gh repo clone

**URL:** https://cli.github.com/manual/gh_repo_clone

**Contents:**
- gh repo clone
  - Options
  - Examples
  - See also
  - In use
    - Using OWNER/REPO syntax
    - Using other selectors

Clone a GitHub repository locally. Pass additional git clone flags by listing them after --.

If the OWNER/ portion of the OWNER/REPO repository argument is omitted, it defaults to the name of the authenticating user.

When a protocol scheme is not provided in the repository argument, the git_protocol will be chosen from your configuration, which can be checked via gh config get git_protocol. If the protocol scheme is provided, the repository will be cloned using the specified protocol.

If the repository is a fork, its parent repository will be added as an additional git remote called upstream. The remote name can be configured using --upstream-remote-name. The --upstream-remote-name option supports an @owner value which will name the remote after the owner of the parent repository.

If the repository is a fork, its parent repository will be set as the default remote repository.

You can clone any repository using OWNER/REPO syntax.

You can also use GitHub URLs to clone repositories.

**Examples:**

Example 1 (unknown):
```unknown
gh repo clone <repository> [<directory>] [-- <gitflags>...]
```

Example 2 (bash):
```bash
# Clone a repository from a specific org
$ gh repo clone cli/cli

# Clone a repository from your own account
$ gh repo clone myrepo

# Clone a repo, overriding git protocol configuration
$ gh repo clone https://github.com/cli/cli
$ gh repo clone git@github.com:cli/cli.git

# Clone a repository to a custom directory
$ gh repo clone cli/cli workspace/cli

# Clone a repository with additional git clone flags
$ gh repo clone cli/cli -- --depth=1
```

Example 3 (unknown):
```unknown
# Cloning a repository
~/Projects$ gh repo clone cli/cli
Cloning into 'cli'...
~/Projects$ cd cli
~/Projects/cli$
```

Example 4 (unknown):
```unknown
# Cloning a repository
~/Projects/my-project$ gh repo clone https://github.com/cli/cli
Cloning into 'cli'...
remote: Enumerating objects: 99, done.
remote: Counting objects: 100% (99/99), done.
remote: Compressing objects: 100% (76/76), done.
remote: Total 21160 (delta 49), reused 35 (delta 18), pack-reused 21061
Receiving objects: 100% (21160/21160), 57.93 MiB | 10.82 MiB/s, done.
Resolving deltas: 100% (16051/16051), done.

~/Projects/my-project$
```

---

## gh repo autolink list

**URL:** https://cli.github.com/manual/gh_repo_autolink_list

**Contents:**
- gh repo autolink list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

Gets all autolink references that are configured for a repository.

Information about autolinks is only available to repository administrators.

id, isAlphanumeric, keyPrefix, urlTemplate

**Examples:**

Example 1 (unknown):
```unknown
gh repo autolink list [flags]
```

---

## gh pr status

**URL:** https://cli.github.com/manual/gh_pr_status

**Contents:**
- gh pr status
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also
  - In use

Show status of relevant pull requests.

The status shows a summary of pull requests that includes information such as pull request number, title, CI checks, reviews, etc.

To see more details of CI checks, run gh pr checks.

additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid, body, changedFiles, closed, closedAt, closingIssuesReferences, comments, commits, createdAt, deletions, files, fullDatabaseId, headRefName, headRefOid, headRepository, headRepositoryOwner, id, isCrossRepository, isDraft, labels, latestReviews, maintainerCanModify, mergeCommit, mergeStateStatus, mergeable, mergedAt, mergedBy, milestone, number, potentialMergeCommit, projectCards, projectItems, reactionGroups, reviewDecision, reviewRequests, reviews, state, statusCheckRollup, title, updatedAt, url

**Examples:**

Example 1 (unknown):
```unknown
gh pr status [flags]
```

Example 2 (unknown):
```unknown
# Viewing the status of your relevant pull requests
~/Projects/my-project$ gh pr status
Current branch
  #12 Remove the test feature [user:patch-2]
   - All checks failing - Review required

Created by you
  You have no open pull requests

Requesting a code review from you
  #13 Fix tests [branch]
  - 3/4 checks failing - Review required
  #15 New feature [branch]
   - Checks passing - Approved

~/Projects/my-project$
```

---

## gh agent-task create

**URL:** https://cli.github.com/manual/gh_agent-task_create

**Contents:**
- gh agent-task create
  - Options
  - Examples
  - See also

Create an agent task (preview)

**Examples:**

Example 1 (unknown):
```unknown
gh agent-task create [<task description>] [flags]
```

Example 2 (bash):
```bash
# Create a task from an inline description
$ gh agent-task create "build me a new app"

# Create a task from an inline description and follow logs
$ gh agent-task create "build me a new app" --follow

# Create a task from a file
$ gh agent-task create -F task-desc.md

# Create a task with problem statement from stdin
$ echo "build me a new app" | gh agent-task create -F -

# Create a task with an editor
$ gh agent-task create

# Create a task with an editor and a file as a template
$ gh agent-task create -F task-desc.md

# Select a different base branch for the PR
$ gh agent-task create "fix errors" --base branch
```

---

## gh project unlink

**URL:** https://cli.github.com/manual/gh_project_unlink

**Contents:**
- gh project unlink
  - Options
  - Examples
  - See also

Unlink a project from a repository or a team

**Examples:**

Example 1 (unknown):
```unknown
gh project unlink [<number>] [flags]
```

Example 2 (bash):
```bash
# Unlink monalisa's project 1 from her repository "my_repo"
$ gh project unlink 1 --owner monalisa --repo my_repo

# Unlink monalisa's organization's project 1 from her team "my_team"
$ gh project unlink 1 --owner my_organization --team my_team

# Unlink monalisa's project 1 from the repository of current directory if neither --repo nor --team is specified
$ gh project unlink 1
```

---

## gh repo

**URL:** https://cli.github.com/manual/gh_repo

**Contents:**
- gh repo
  - General commands
  - Targeted commands
  - Examples
  - See also

Work with GitHub repositories.

**Examples:**

Example 1 (bash):
```bash
$ gh repo create
$ gh repo clone cli/cli
$ gh repo view --web
```

---

## gh project link

**URL:** https://cli.github.com/manual/gh_project_link

**Contents:**
- gh project link
  - Options
  - Examples
  - See also

Link a project to a repository or a team

**Examples:**

Example 1 (unknown):
```unknown
gh project link [<number>] [flags]
```

Example 2 (bash):
```bash
# Link monalisa's project 1 to her repository "my_repo"
$ gh project link 1 --owner monalisa --repo my_repo

# Link monalisa's organization's project 1 to her team "my_team"
$ gh project link 1 --owner my_organization --team my_team

# Link monalisa's project 1 to the repository of current directory if neither --repo nor --team is specified
$ gh project link 1
```

---

## gh repo autolink view

**URL:** https://cli.github.com/manual/gh_repo_autolink_view

**Contents:**
- gh repo autolink view
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also

View an autolink reference for a repository.

id, isAlphanumeric, keyPrefix, urlTemplate

**Examples:**

Example 1 (unknown):
```unknown
gh repo autolink view <id> [flags]
```

---

## gh label clone

**URL:** https://cli.github.com/manual/gh_label_clone

**Contents:**
- gh label clone
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Clones labels from a source repository to a destination repository on GitHub. By default, the destination repository is the current repository.

All labels from the source repository will be copied to the destination repository. Labels in the destination repository that are not in the source repository will not be deleted or modified.

Labels from the source repository that already exist in the destination repository will be skipped. You can overwrite existing labels in the destination repository using the --force flag.

**Examples:**

Example 1 (unknown):
```unknown
gh label clone <source-repository> [flags]
```

Example 2 (bash):
```bash
# Clone and overwrite labels from cli/cli repository into the current repository
$ gh label clone cli/cli --force

# Clone labels from cli/cli repository into a octocat/cli repository
$ gh label clone cli/cli --repo octocat/cli
```

---

## gh repo list

**URL:** https://cli.github.com/manual/gh_repo_list

**Contents:**
- gh repo list
  - Options
  - ALIASES
  - JSON Fields
  - See also

List repositories owned by a user or organization.

Note that the list will only include repositories owned by the provided argument, and the --fork or --source flags will not traverse ownership boundaries. For example, when listing the forks in an organization, the output would not include those owned by individual users.

archivedAt, assignableUsers, codeOfConduct, contactLinks, createdAt, defaultBranchRef, deleteBranchOnMerge, description, diskUsage, forkCount, fundingLinks, hasDiscussionsEnabled, hasIssuesEnabled, hasProjectsEnabled, hasWikiEnabled, homepageUrl, id, isArchived, isBlankIssuesEnabled, isEmpty, isFork, isInOrganization, isMirror, isPrivate, isSecurityPolicyEnabled, isTemplate, isUserConfigurationRepository, issueTemplates, issues, labels, languages, latestRelease, licenseInfo, mentionableUsers, mergeCommitAllowed, milestones, mirrorUrl, name, nameWithOwner, openGraphImageUrl, owner, parent, primaryLanguage, projects, projectsV2, pullRequestTemplates, pullRequests, pushedAt, rebaseMergeAllowed, repositoryTopics, securityPolicyUrl, squashMergeAllowed, sshUrl, stargazerCount, templateRepository, updatedAt, url, usesCustomOpenGraphImage, viewerCanAdminister, viewerDefaultCommitEmail, viewerDefaultMergeMethod, viewerHasStarred, viewerPermission, viewerPossibleCommitEmails, viewerSubscription, visibility, watchers

**Examples:**

Example 1 (unknown):
```unknown
gh repo list [<owner>] [flags]
```

---

## gh issue unpin

**URL:** https://cli.github.com/manual/gh_issue_unpin

**Contents:**
- gh issue unpin
  - Options inherited from parent commands
  - Examples
  - See also

Unpin an issue from a repository.

The issue can be specified by issue number or URL.

**Examples:**

Example 1 (unknown):
```unknown
gh issue unpin {<number> | <url>}
```

Example 2 (bash):
```bash
# Unpin issue from the current repository
$ gh issue unpin 23

# Unpin issue by URL
$ gh issue unpin https://github.com/owner/repo/issues/23

# Unpin an issue from specific repository
$ gh issue unpin 23 --repo owner/repo
```

---

## gh repo view

**URL:** https://cli.github.com/manual/gh_repo_view

**Contents:**
- gh repo view
  - Options
  - JSON Fields
  - See also
  - In use
    - In terminal
    - In the browser
    - With no arguments

Display the description and the README of a GitHub repository.

With no argument, the repository for the current directory is displayed.

With --web, open the repository in a web browser instead.

With --branch, view a specific branch of the repository.

archivedAt, assignableUsers, codeOfConduct, contactLinks, createdAt, defaultBranchRef, deleteBranchOnMerge, description, diskUsage, forkCount, fundingLinks, hasDiscussionsEnabled, hasIssuesEnabled, hasProjectsEnabled, hasWikiEnabled, homepageUrl, id, isArchived, isBlankIssuesEnabled, isEmpty, isFork, isInOrganization, isMirror, isPrivate, isSecurityPolicyEnabled, isTemplate, isUserConfigurationRepository, issueTemplates, issues, labels, languages, latestRelease, licenseInfo, mentionableUsers, mergeCommitAllowed, milestones, mirrorUrl, name, nameWithOwner, openGraphImageUrl, owner, parent, primaryLanguage, projects, projectsV2, pullRequestTemplates, pullRequests, pushedAt, rebaseMergeAllowed, repositoryTopics, securityPolicyUrl, squashMergeAllowed, sshUrl, stargazerCount, templateRepository, updatedAt, url, usesCustomOpenGraphImage, viewerCanAdminister, viewerDefaultCommitEmail, viewerDefaultMergeMethod, viewerHasStarred, viewerPermission, viewerPossibleCommitEmails, viewerSubscription, visibility, watchers

By default, we will display items in the terminal.

Quickly open an item in the browser using --web or -w

We will display the repository you're currently in.

**Examples:**

Example 1 (unknown):
```unknown
gh repo view [<repository>] [flags]
```

Example 2 (unknown):
```unknown
# Viewing a repository in terminal
~/Projects/my-project$ gh repo view owner/repo
owner/repo
Repository description

  Repository README

View this repository on GitHub: https://github.com/owner/repo/
~/Projects/my-project$
```

Example 3 (unknown):
```unknown
# Viewing a repository in the browser
~/Projects$ gh repo view owner/repo --web
Opening https://github.com/owner/repo/ in your browser.
~/Projects$
```

Example 4 (unknown):
```unknown
# Viewing the repository you're in
~/Projects/my-project$ gh repo view
owner/my-project
Repository description

  Repository README

View this repository on GitHub: https://github.com/owner/repo/
~/Projects/my-project$
```

---

## gh gist clone

**URL:** https://cli.github.com/manual/gh_gist_clone

**Contents:**
- gh gist clone
  - See also

Clone a GitHub gist locally.

A gist can be supplied as argument in either of the following formats:

Pass additional git clone flags by listing them after --.

**Examples:**

Example 1 (unknown):
```unknown
gh gist clone <gist> [<directory>] [-- <gitflags>...]
```

---

## gh codespace create

**URL:** https://cli.github.com/manual/gh_codespace_create

**Contents:**
- gh codespace create
  - Options
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh codespace create [flags]
```

---

## gh repo delete

**URL:** https://cli.github.com/manual/gh_repo_delete

**Contents:**
- gh repo delete
  - Options
  - See also

Delete a GitHub repository.

With no argument, deletes the current repository. Otherwise, deletes the specified repository.

For safety, when no repository argument is provided, the --yes flag is ignored and you will be prompted for confirmation. To delete the current repository non-interactively, specify it explicitly (e.g., gh repo delete owner/repo --yes).

Deletion requires authorization with the delete_repo scope. To authorize, run gh auth refresh -s delete_repo

**Examples:**

Example 1 (unknown):
```unknown
gh repo delete [<repository>] [flags]
```

---

## gh repo deploy-key add

**URL:** https://cli.github.com/manual/gh_repo_deploy-key_add

**Contents:**
- gh repo deploy-key add
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Add a deploy key to a GitHub repository.

Note that any key added by gh will be associated with the current authentication token. If you de-authorize the GitHub CLI app or authentication token from your account, any deploy keys added by GitHub CLI will be removed as well.

**Examples:**

Example 1 (unknown):
```unknown
gh repo deploy-key add <key-file> [flags]
```

Example 2 (bash):
```bash
# Generate a passwordless SSH key and add it as a deploy key to a repository
$ ssh-keygen -t ed25519 -C "my description" -N "" -f ~/.ssh/gh-test
$ gh repo deploy-key add ~/.ssh/gh-test.pub
```

---

## gh repo gitignore view

**URL:** https://cli.github.com/manual/gh_repo_gitignore_view

**Contents:**
- gh repo gitignore view
  - Examples
  - See also

View an available repository .gitignore template.

<template> is a case-sensitive .gitignore template name.

For a list of available templates, run gh repo gitignore list.

**Examples:**

Example 1 (unknown):
```unknown
gh repo gitignore view <template>
```

Example 2 (bash):
```bash
# View the Go gitignore template
$ gh repo gitignore view Go

# View the Python gitignore template
$ gh repo gitignore view Python

# Create a new .gitignore file using the Go template
$ gh repo gitignore view Go > .gitignore

# Create a new .gitignore file using the Python template
$ gh repo gitignore view Python > .gitignore
```

---

## gh issue edit

**URL:** https://cli.github.com/manual/gh_issue_edit

**Contents:**
- gh issue edit
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Edit one or more issues within the same repository.

Editing issues' projects requires authorization with the project scope. To authorize, run gh auth refresh -s project.

The --add-assignee and --remove-assignee flags both support the following special values:

**Examples:**

Example 1 (unknown):
```unknown
gh issue edit {<numbers> | <urls>} [flags]
```

Example 2 (bash):
```bash
$ gh issue edit 23 --title "I found a bug" --body "Nothing works"
$ gh issue edit 23 --add-label "bug,help wanted" --remove-label "core"
$ gh issue edit 23 --add-assignee "@me" --remove-assignee monalisa,hubot
$ gh issue edit 23 --add-assignee "@copilot"
$ gh issue edit 23 --add-project "Roadmap" --remove-project v1,v2
$ gh issue edit 23 --milestone "Version 1"
$ gh issue edit 23 --remove-milestone
$ gh issue edit 23 --body-file body.txt
$ gh issue edit 23 34 --add-label "help wanted"
```

---

## gh release list

**URL:** https://cli.github.com/manual/gh_release_list

**Contents:**
- gh release list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List releases in a repository

createdAt, isDraft, isLatest, isPrerelease, name, publishedAt, tagName

**Examples:**

Example 1 (unknown):
```unknown
gh release list [flags]
```

---

## gh variable list

**URL:** https://cli.github.com/manual/gh_variable_list

**Contents:**
- gh variable list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List variables on one of the following levels:

createdAt, name, numSelectedRepos, selectedReposURL, updatedAt, value, visibility

**Examples:**

Example 1 (unknown):
```unknown
gh variable list [flags]
```

---

## gh project item-create

**URL:** https://cli.github.com/manual/gh_project_item-create

**Contents:**
- gh project item-create
  - Options
  - Examples
  - See also

Create a draft issue item in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project item-create [<number>] [flags]
```

Example 2 (bash):
```bash
# Create a draft issue in the current user's project "1"
$ gh project item-create 1 --owner "@me" --title "new item" --body "new item body"
```

---

## gh repo deploy-key

**URL:** https://cli.github.com/manual/gh_repo_deploy-key

**Contents:**
- gh repo deploy-key
  - Available commands
  - Options
  - See also

Manage deploy keys in a repository

---

## gh repo sync

**URL:** https://cli.github.com/manual/gh_repo_sync

**Contents:**
- gh repo sync
  - Options
  - Examples
  - See also

Sync destination repository from source repository. Syncing uses the default branch of the source repository to update the matching branch on the destination repository so they are equal. A fast forward update will be used except when the --force flag is specified, then the two branches will be synced using a hard reset.

Without an argument, the local repository is selected as the destination repository.

The source repository is the parent of the destination repository by default. This can be overridden with the --source flag.

**Examples:**

Example 1 (unknown):
```unknown
gh repo sync [<destination-repository>] [flags]
```

Example 2 (bash):
```bash
# Sync local repository from remote parent
$ gh repo sync

# Sync local repository from remote parent on specific branch
$ gh repo sync --branch v1

# Sync remote fork from its parent
$ gh repo sync owner/cli-fork

# Sync remote repository from another remote repository
$ gh repo sync owner/repo --source owner2/repo2
```

---

## gh codespace list

**URL:** https://cli.github.com/manual/gh_codespace_list

**Contents:**
- gh codespace list
  - Options
  - ALIASES
  - JSON Fields
  - See also

List codespaces of the authenticated user.

Alternatively, organization administrators may list all codespaces billed to the organization.

gh cs ls, gh codespace ls

createdAt, displayName, gitStatus, lastUsedAt, machineName, name, owner, repository, state, vscsTarget

**Examples:**

Example 1 (unknown):
```unknown
gh codespace list [flags]
```

---

## gh variable

**URL:** https://cli.github.com/manual/gh_variable

**Contents:**
- gh variable
  - Available commands
  - Options
  - See also

Variables can be set at the repository, environment or organization level for use in GitHub Actions or Dependabot. Run gh help variable set to learn how to get started.

---

## gh pr checkout

**URL:** https://cli.github.com/manual/gh_pr_checkout

**Contents:**
- gh pr checkout
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also
  - In use
    - Using pull request number
    - Using other selectors

Check out a pull request in git

You can check out any pull request, including from forks, in a repository using its pull request number

You can also use URLs and branch names to checkout pull requests.

**Examples:**

Example 1 (unknown):
```unknown
gh pr checkout [<number> | <url> | <branch>] [flags]
```

Example 2 (bash):
```bash
# Interactively select a PR from the 10 most recent to check out
$ gh pr checkout

# Checkout a specific PR
$ gh pr checkout 32
$ gh pr checkout https://github.com/OWNER/REPO/pull/32
$ gh pr checkout feature
```

Example 3 (unknown):
```unknown
// Checking out a pull request locally
~/Projects/my-project$ gh pr checkout 12
remote: Enumerating objects: 66, done.
remote: Counting objects: 100% (66/66), done.
remote: Total 83 (delta 66), reused 66 (delta 66), pack-reused 17
Unpacking objects: 100% (83/83), done.
From https://github.com/owner/repo
 * [new ref]             refs/pull/8896/head -> patch-2
M       README.md
Switched to branch 'patch-2'

~/Projects/my-project$
```

Example 4 (unknown):
```unknown
// Checking out a pull request locally
~/Projects/my-project$ gh pr checkout branch-name
Switched to branch 'branch-name'
Your branch is up to date with 'origin/branch-name'.
Already up to date.

~/Projects/my-project$
```

---

## gh repo archive

**URL:** https://cli.github.com/manual/gh_repo_archive

**Contents:**
- gh repo archive
  - Options
  - See also

Archive a GitHub repository.

With no argument, archives the current repository.

**Examples:**

Example 1 (unknown):
```unknown
gh repo archive [<repository>] [flags]
```

---

## gh release create

**URL:** https://cli.github.com/manual/gh_release_create

**Contents:**
- gh release create
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also

Create a new GitHub Release for a repository.

A list of asset files may be given to upload to the new release. To define a display label for an asset, append text starting with # after the file name.

If a matching git tag does not yet exist, one will automatically get created from the latest state of the default branch. Use --target to point to a different branch or commit for the automatic tag creation. Use --verify-tag to abort the release if the tag doesn't already exist. To fetch the new tag locally after the release, do git fetch --tags origin.

To create a release from an annotated git tag, first create one locally with git, push the tag to GitHub, then run this command. Use --notes-from-tag to get the release notes from the annotated git tag. If the tag is not annotated, the commit message will be used instead.

Use --generate-notes to automatically generate notes using GitHub Release Notes API. When using automatically generated release notes, a release title will also be automatically generated unless a title was explicitly passed. Additional release notes can be prepended to automatically generated notes by using the --notes flag.

By default, the release is created even if there are no new commits since the last release. This may result in the same or duplicate release which may not be desirable in some cases. Use --fail-on-no-commits to fail if no new commits are available. This flag has no effect if there are no existing releases or this is the very first release.

**Examples:**

Example 1 (unknown):
```unknown
gh release create [<tag>] [<filename>... | <pattern>...]
```

Example 2 (bash):
```bash
# Interactively create a release
$ gh release create

# Interactively create a release from specific tag
$ gh release create v1.2.3

# Non-interactively create a release
$ gh release create v1.2.3 --notes "bugfix release"

# Use automatically generated via GitHub Release Notes API release notes
$ gh release create v1.2.3 --generate-notes

# Use release notes from a file
$ gh release create v1.2.3 -F release-notes.md

# Use tag annotation or associated commit message as notes
$ gh release create v1.2.3 --notes-from-tag

# Don't mark the release as latest
$ gh release create v1.2.3 --latest=false

# Upload all tarballs in a directory as release assets
$ gh release create v1.2.3 ./dist/*.tgz

# Upload a release asset with a display label
$ gh release create v1.2.3 '/path/to/asset.zip#My display label'

# Create a release and start a discussion
$ gh release create v1.2.3 --discussion-category "General"

# Create a release only if there are new commits available since the last release
$ gh release create v1.2.3 --fail-on-no-commits
```

---

## gh issue pin

**URL:** https://cli.github.com/manual/gh_issue_pin

**Contents:**
- gh issue pin
  - Options inherited from parent commands
  - Examples
  - See also

Pin an issue to a repository.

The issue can be specified by issue number or URL.

**Examples:**

Example 1 (unknown):
```unknown
gh issue pin {<number> | <url>}
```

Example 2 (bash):
```bash
# Pin an issue to the current repository
$ gh issue pin 23

# Pin an issue by URL
$ gh issue pin https://github.com/owner/repo/issues/23

# Pin an issue to specific repository
$ gh issue pin 23 --repo owner/repo
```

---

## gh repo deploy-key delete

**URL:** https://cli.github.com/manual/gh_repo_deploy-key_delete

**Contents:**
- gh repo deploy-key delete
  - Options inherited from parent commands
  - See also

Delete a deploy key from a GitHub repository

**Examples:**

Example 1 (unknown):
```unknown
gh repo deploy-key delete <key-id>
```

---

## gh extension

**URL:** https://cli.github.com/manual/gh_extension

**Contents:**
- gh extension
  - Available commands
  - ALIASES
  - See also

GitHub CLI extensions are repositories that provide additional gh commands.

The name of the extension repository must start with gh- and it must contain an executable of the same name. All arguments passed to the gh <extname> invocation will be forwarded to the gh-<extname> executable of the extension.

An extension cannot override any of the core gh commands. If an extension name conflicts with a core gh command, you can use gh extension exec <extname>.

When an extension is executed, gh will check for new versions once every 24 hours and display an upgrade notice. See gh help environment for information on disabling extension notices.

For the list of available extensions, see https://github.com/topics/gh-extension.

gh ext, gh extensions

---

## gh ruleset check

**URL:** https://cli.github.com/manual/gh_ruleset_check

**Contents:**
- gh ruleset check
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

View information about GitHub rules that apply to a given branch.

The provided branch name does not need to exist; rules will be displayed that would apply to a branch with that name. All rules are returned regardless of where they are configured.

If no branch name is provided, then the current branch will be used.

The --default flag can be used to view rules that apply to the default branch of the repository.

**Examples:**

Example 1 (unknown):
```unknown
gh ruleset check [<branch>] [flags]
```

Example 2 (bash):
```bash
# View all rules that apply to the current branch
$ gh ruleset check

# View all rules that apply to a branch named "my-branch" in a different repository
$ gh ruleset check my-branch --repo owner/repo

# View all rules that apply to the default branch in a different repository
$ gh ruleset check --default --repo owner/repo

# View a ruleset configured in a different repository or any of its parents
$ gh ruleset view 23 --repo owner/repo

# View an organization-level ruleset
$ gh ruleset view 23 --org my-org
```

---

## gh codespace delete

**URL:** https://cli.github.com/manual/gh_codespace_delete

**Contents:**
- gh codespace delete
  - Options
  - See also

Delete codespaces based on selection criteria.

All codespaces for the authenticated user can be deleted, as well as codespaces for a specific repository. Alternatively, only codespaces older than N days can be deleted.

Organization administrators may delete any codespace billed to the organization.

**Examples:**

Example 1 (unknown):
```unknown
gh codespace delete [flags]
```

---

## gh pr list

**URL:** https://cli.github.com/manual/gh_pr_list

**Contents:**
- gh pr list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - Examples
  - See also
  - In use
    - Default behavior
    - Filtering with flags

List pull requests in a GitHub repository. By default, this only lists open PRs.

The search query syntax is documented here: https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests

On supported GitHub hosts, advanced issue search syntax can be used in the --search query. For more information about advanced issue search, see: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests#building-advanced-filters-for-issues

additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid, body, changedFiles, closed, closedAt, closingIssuesReferences, comments, commits, createdAt, deletions, files, fullDatabaseId, headRefName, headRefOid, headRepository, headRepositoryOwner, id, isCrossRepository, isDraft, labels, latestReviews, maintainerCanModify, mergeCommit, mergeStateStatus, mergeable, mergedAt, mergedBy, milestone, number, potentialMergeCommit, projectCards, projectItems, reactionGroups, reviewDecision, reviewRequests, reviews, state, statusCheckRollup, title, updatedAt, url

You will see the most recent 30 open items.

You can use flags to filter the list for your specific use cases.

**Examples:**

Example 1 (unknown):
```unknown
gh pr list [flags]
```

Example 2 (bash):
```bash
# List PRs authored by you
$ gh pr list --author "@me"

# List PRs with a specific head branch name
$ gh pr list --head "typo"

# List only PRs with all of the given labels
$ gh pr list --label bug --label "priority 1"

# Filter PRs using search syntax
$ gh pr list --search "status:success review:required"

# Find a PR that introduced a given commit
$ gh pr list --search "<SHA>" --state merged
```

Example 3 (unknown):
```unknown
# Viewing a list of open pull requests
~/Projects/my-project$ gh pr list

Pull requests for owner/repo

#14  Upgrade to Prettier 1.19                           prettier
#14  Extend arrow navigation in lists for MacOS         arrow-nav
#13  Add Support for Windows Automatic Dark Mode        dark-mode
#8   Create and use keyboard shortcut react component   shortcut

~/Projects/my-project$
```

Example 4 (unknown):
```unknown
# Viewing a list of closed pull requests assigned to a user
~/Projects/my-project$ gh pr list --state closed --assignee user

Pull requests for owner/repo

#13  Upgrade to Electron 7         electron-7
#8   Release Notes Writing Guide   release-notes

~/Projects/my-project$
```

---

## gh issue transfer

**URL:** https://cli.github.com/manual/gh_issue_transfer

**Contents:**
- gh issue transfer
  - Options inherited from parent commands
  - See also

Transfer issue to another repository

**Examples:**

Example 1 (unknown):
```unknown
gh issue transfer {<number> | <url>} <destination-repo>
```

---

## gh extension exec

**URL:** https://cli.github.com/manual/gh_extension_exec

**Contents:**
- gh extension exec
  - Examples
  - See also

Execute an extension using the short name. For example, if the extension repository is owner/gh-extension, you should pass extension. You can use this command when the short name conflicts with a core gh command.

All arguments after the extension name will be forwarded to the executable of the extension.

**Examples:**

Example 1 (unknown):
```unknown
gh extension exec <name> [args]
```

Example 2 (bash):
```bash
# Execute a label extension instead of the core gh label command
$ gh extension exec label
```

---

## gh extension create

**URL:** https://cli.github.com/manual/gh_extension_create

**Contents:**
- gh extension create
  - Options
  - Examples
  - See also

Create a new extension

**Examples:**

Example 1 (unknown):
```unknown
gh extension create [<name>] [flags]
```

Example 2 (bash):
```bash
# Use interactively
$ gh extension create

# Create a script-based extension
$ gh extension create foobar

# Create a Go extension
$ gh extension create --precompiled=go foobar

# Create a non-Go precompiled extension
$ gh extension create --precompiled=other foobar
```

---

## gh repo create

**URL:** https://cli.github.com/manual/gh_repo_create

**Contents:**
- gh repo create
  - Options
  - ALIASES
  - Examples
  - See also

Create a new GitHub repository.

To create a repository interactively, use gh repo create with no arguments.

To create a remote repository non-interactively, supply the repository name and one of --public, --private, or --internal. Pass --clone to clone the new repository locally.

If the OWNER/ portion of the OWNER/REPO name argument is omitted, it defaults to the name of the authenticating user.

To create a remote repository from an existing local repository, specify the source directory with --source. By default, the remote repository name will be the name of the source directory.

Pass --push to push any local commits to the new repository. If the repo is bare, this will mirror all refs.

For language or platform .gitignore templates to use with --gitignore, https://github.com/github/gitignore.

For license keywords to use with --license, run gh repo license list or visit https://choosealicense.com.

The repo is created with the configured repository default branch, see https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-user-account-settings/managing-the-default-branch-name-for-your-repositories.

**Examples:**

Example 1 (unknown):
```unknown
gh repo create [<name>] [flags]
```

Example 2 (bash):
```bash
# Create a repository interactively
$ gh repo create

# Create a new remote repository and clone it locally
$ gh repo create my-project --public --clone

# Create a new remote repository in a different organization
$ gh repo create my-org/my-project --public

# Create a remote repository from the current directory
$ gh repo create my-project --private --source=. --remote=upstream
```

---

## gh issue list

**URL:** https://cli.github.com/manual/gh_issue_list

**Contents:**
- gh issue list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - Examples
  - See also
  - In use
    - Default behavior
    - Filtering with flags

List issues in a GitHub repository. By default, this only lists open issues.

The search query syntax is documented here: https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests

On supported GitHub hosts, advanced issue search syntax can be used in the --search query. For more information about advanced issue search, see: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests#building-advanced-filters-for-issues

assignees, author, body, closed, closedAt, closedByPullRequestsReferences, comments, createdAt, id, isPinned, labels, milestone, number, projectCards, projectItems, reactionGroups, state, stateReason, title, updatedAt, url

You will see the most recent 30 open items.

You can use flags to filter the list for your specific use cases.

**Examples:**

Example 1 (unknown):
```unknown
gh issue list [flags]
```

Example 2 (bash):
```bash
$ gh issue list --label "bug" --label "help wanted"
$ gh issue list --author monalisa
$ gh issue list --assignee "@me"
$ gh issue list --milestone "The big 1.0"
$ gh issue list --search "error no:assignee sort:created-asc"
$ gh issue list --state all
```

Example 3 (unknown):
```unknown
# Viewing a list of open issues
~/Projects/my-project$ gh issue list

Issues for owner/repo

#14  Update the remote url if it changed  (bug)
#14  PR commands on a detached head       (enhancement)
#13  Support for GitHub Enterprise        (wontfix)
#8   Add an easier upgrade command        (bug)

~/Projects/my-project$
```

Example 4 (unknown):
```unknown
# Viewing a list of closed issues assigned to a user
~/Projects/my-project$ gh issue list --state closed --assignee user

Issues for owner/repo

#13  Enable discarding submodule changes  (bug)
#8   Upgrade to latest react              (upgrade)

~/Projects/my-project$
```

---

## gh repo deploy-key list

**URL:** https://cli.github.com/manual/gh_repo_deploy-key_list

**Contents:**
- gh repo deploy-key list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List deploy keys in a GitHub repository

gh repo deploy-key ls

createdAt, id, key, readOnly, title

**Examples:**

Example 1 (unknown):
```unknown
gh repo deploy-key list [flags]
```

---

## gh codespace view

**URL:** https://cli.github.com/manual/gh_codespace_view

**Contents:**
- gh codespace view
  - Options
  - JSON Fields
  - Examples
  - See also

View details about a codespace

billableOwner, createdAt, devcontainerPath, displayName, environmentId, gitStatus, idleTimeoutMinutes, lastUsedAt, location, machineDisplayName, machineName, name, owner, prebuild, recentFolders, repository, retentionExpiresAt, retentionPeriodDays, state, vscsTarget

**Examples:**

Example 1 (unknown):
```unknown
gh codespace view [flags]
```

Example 2 (bash):
```bash
# Select a codespace from a list of all codespaces you own
$ gh cs view

# View the details of a specific codespace
$ gh cs view -c codespace-name-12345

# View the list of all available fields for a codespace
$ gh cs view --json

# View specific fields for a codespace
$ gh cs view --json displayName,machineDisplayName,state
```

---

## gh label create

**URL:** https://cli.github.com/manual/gh_label_create

**Contents:**
- gh label create
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Create a new label on GitHub, or update an existing one with --force.

Must specify name for the label. The description and color are optional. If a color isn't provided, a random one will be chosen.

The label color needs to be 6 character hex value.

**Examples:**

Example 1 (unknown):
```unknown
gh label create <name> [flags]
```

Example 2 (bash):
```bash
# Create new bug label
$ gh label create bug --description "Something isn't working" --color E99695
```

---

## gh variable get

**URL:** https://cli.github.com/manual/gh_variable_get

**Contents:**
- gh variable get
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also

Get a variable on one of the following levels:

createdAt, name, numSelectedRepos, selectedReposURL, updatedAt, value, visibility

**Examples:**

Example 1 (unknown):
```unknown
gh variable get <variable-name> [flags]
```

---

## gh project create

**URL:** https://cli.github.com/manual/gh_project_create

**Contents:**
- gh project create
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project create [flags]
```

Example 2 (bash):
```bash
# Create a new project owned by login monalisa
$ gh project create --owner monalisa --title "a new project"
```

---

## gh pr create

**URL:** https://cli.github.com/manual/gh_pr_create

**Contents:**
- gh pr create
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also
  - In use
    - Interactively
    - With flags
    - In the browser

Create a pull request on GitHub.

Upon success, the URL of the created pull request will be printed.

When the current branch isn't fully pushed to a git remote, a prompt will ask where to push the branch and offer an option to fork the base repository. Use --head to explicitly skip any forking or pushing behavior.

--head supports <user>:<branch> syntax to select a head repo owned by <user>. Using an organization as the <user> is currently not supported. For more information, see https://github.com/cli/cli/issues/10093

A prompt will also ask for the title and the body of the pull request. Use --title and --body to skip this, or use --fill to autofill these values from git commits. It's important to notice that if the --title and/or --body are also provided alongside --fill, the values specified by --title and/or --body will take precedence and overwrite any autofilled content.

The base branch for the created PR can be specified using the --base flag. If not provided, the value of gh-merge-base git branch config will be used. If not configured, the repository's default branch will be used. Run git config branch.{current}.gh-merge-base {base} to configure the current branch to use the specified merge base.

Link an issue to the pull request by referencing the issue in the body of the pull request. If the body text mentions Fixes #123 or Closes #123, the referenced issue will automatically get closed when the pull request gets merged.

By default, users with write access to the base repository can push new commits to the head branch of the pull request. Disable this with --no-maintainer-edit.

Adding a pull request to projects requires authorization with the project scope. To authorize, run gh auth refresh -s project.

This command will automatically create a fork for you if you're in a repository that you don't have permission to push to.

**Examples:**

Example 1 (unknown):
```unknown
gh pr create [flags]
```

Example 2 (bash):
```bash
$ gh pr create --title "The bug is fixed" --body "Everything works again"
$ gh pr create --reviewer monalisa,hubot  --reviewer myorg/team-name
$ gh pr create --project "Roadmap"
$ gh pr create --base develop --head monalisa:feature
$ gh pr create --template "pull_request_template.md"
```

Example 3 (unknown):
```unknown
# Create a pull request interactively
~/Projects/my-project$ gh pr create
Creating pull request for feature-branch into main in owner/repo
? Title My new pull request
? Body [(e) to launch nano, enter to skip]
http://github.com/owner/repo/pull/1
~/Projects/my-project$
```

Example 4 (unknown):
```unknown
# Create a pull request using flags
~/Projects/my-project$ gh pr create --title "Pull request title" --body "Pull request body"
http://github.com/owner/repo/pull/1
~/Projects/my-project$
```

---

## gh repo autolink delete

**URL:** https://cli.github.com/manual/gh_repo_autolink_delete

**Contents:**
- gh repo autolink delete
  - Options
  - Options inherited from parent commands
  - See also

Delete an autolink reference for a repository.

**Examples:**

Example 1 (unknown):
```unknown
gh repo autolink delete <id> [flags]
```

---

## gh api

**URL:** https://cli.github.com/manual/gh_api

**Contents:**
- gh api
  - Options
  - Examples
  - See also

Makes an authenticated HTTP request to the GitHub API and prints the response.

The endpoint argument should either be a path of a GitHub API v3 endpoint, or graphql to access the GitHub API v4.

Placeholder values {owner}, {repo}, and {branch} in the endpoint argument will get replaced with values from the repository of the current directory or the repository specified in the GH_REPO environment variable. Note that in some shells, for example PowerShell, you may need to enclose any value that contains {...} in quotes to prevent the shell from applying special meaning to curly braces.

The -p/--preview flag enables opting into previews, which are feature-flagged, experimental API endpoints or behaviors. The API expects opt-in via the Accept header with format application/vnd.github.<preview-name>-preview+json and this command facilitates that via --preview <preview-name>. To send a request for the corsair and scarlet witch previews, you could use -p corsair,scarlet-witch or --preview corsair --preview scarlet-witch.

The default HTTP request method is GET normally and POST if any parameters were added. Override the method with --method.

Pass one or more -f/--raw-field values in key=value format to add static string parameters to the request payload. To add non-string or placeholder-determined values, see -F/--field below. Note that adding request parameters will automatically switch the request method to POST. To send the parameters as a GET query string instead, use --method GET.

The -F/--field flag has magic type conversion based on the format of the value:

For GraphQL requests, all fields other than query and operationName are interpreted as GraphQL variables.

To pass nested parameters in the request payload, use key[subkey]=value syntax when declaring fields. To pass nested values as arrays, declare multiple fields with the syntax key[]=value1, key[]=value2. To pass an empty array, use key[] without a value.

To pass pre-constructed JSON or payloads in other formats, a request body may be read from file specified by --input. Use - to read from standard input. When passing the request body this way, any parameters specified via field flags are added to the query string of the endpoint URL.

In --paginate mode, all pages of results will sequentially be requested until there are no more pages of results. For GraphQL requests, this requires that the original query accepts an $endCursor: String variable and that it fetches the pageInfo{ hasNextPage, endCursor } set of fields from a collection. Each page is a separate JSON array or object. Pass --slurp to wrap all pages of JSON arrays or objects into an outer JSON array.

**Examples:**

Example 1 (unknown):
```unknown
gh api <endpoint> [flags]
```

Example 2 (bash):
```bash
# List releases in the current repository
$ gh api repos/{owner}/{repo}/releases

# Post an issue comment
$ gh api repos/{owner}/{repo}/issues/123/comments -f body='Hi from CLI'

# Post nested parameter read from a file
$ gh api gists -F 'files[myfile.txt][content]=@myfile.txt'

# Add parameters to a GET request
$ gh api -X GET search/issues -f q='repo:cli/cli is:open remote'

# Set a custom HTTP header
$ gh api -H 'Accept: application/vnd.github.v3.raw+json' ...

# Opt into GitHub API previews
$ gh api --preview baptiste,nebula ...

# Print only specific fields from the response
$ gh api repos/{owner}/{repo}/issues --jq '.[].title'

# Use a template for the output
$ gh api repos/{owner}/{repo}/issues --template \
  '{{range .}}{{.title}} ({{.labels | pluck "name" | join ", " | color "yellow"}}){{"\n"}}{{end}}'

# Update allowed values of the "environment" custom property in a deeply nested array
$ gh api -X PATCH /orgs/{org}/properties/schema \
   -F 'properties[][property_name]=environment' \
   -F 'properties[][default_value]=production' \
   -F 'properties[][allowed_values][]=staging' \
   -F 'properties[][allowed_values][]=production'

# List releases with GraphQL
$ gh api graphql -F owner='{owner}' -F name='{repo}' -f query='
  query($name: String!, $owner: String!) {
    repository(owner: $owner, name: $name) {
      releases(last: 3) {
        nodes { tagName }
      }
    }
  }
'

# List all repositories for a user
$ gh api graphql --paginate -f query='
  query($endCursor: String) {
    viewer {
      repositories(first: 100, after: $endCursor) {
        nodes { nameWithOwner }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
'

# Get the percentage of forks for the current user
$ gh api graphql --paginate --slurp -f query='
  query($endCursor: String) {
    viewer {
      repositories(first: 100, after: $endCursor) {
        nodes { isFork }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
' | jq 'def count(e): reduce e as $_ (0;.+1);
[.[].data.viewer.repositories.nodes[]] as $r | count(select($r[].isFork))/count($r[])'
```

---

## gh ruleset list

**URL:** https://cli.github.com/manual/gh_ruleset_list

**Contents:**
- gh ruleset list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also

List GitHub rulesets for a repository or organization.

If no options are provided, the current repository's rulesets are listed. You can query a different repository's rulesets by using the --repo flag. You can also use the --org flag to list rulesets configured for the provided organization.

Use the --parents flag to control whether rulesets configured at higher levels that also apply to the provided repository or organization should be returned. The default is true.

Your access token must have the admin:org scope to use the --org flag, which can be granted by running gh auth refresh -s admin:org.

gh ruleset ls, gh rs ls

**Examples:**

Example 1 (unknown):
```unknown
gh ruleset list [flags]
```

Example 2 (bash):
```bash
# List rulesets in the current repository
$ gh ruleset list

# List rulesets in a different repository, including those configured at higher levels
$ gh ruleset list --repo owner/repo --parents

# List rulesets in an organization
$ gh ruleset list --org org-name
```

---

## gh issue create

**URL:** https://cli.github.com/manual/gh_issue_create

**Contents:**
- gh issue create
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also
  - In use
    - Interactively
    - With flags
    - In the browser

Create an issue on GitHub.

Adding an issue to projects requires authorization with the project scope. To authorize, run gh auth refresh -s project.

The --assignee flag supports the following special values:

**Examples:**

Example 1 (unknown):
```unknown
gh issue create [flags]
```

Example 2 (bash):
```bash
$ gh issue create --title "I found a bug" --body "Nothing works"
$ gh issue create --label "bug,help wanted"
$ gh issue create --label bug --label "help wanted"
$ gh issue create --assignee monalisa,hubot
$ gh issue create --assignee "@me"
$ gh issue create --assignee "@copilot"
$ gh issue create --project "Roadmap"
$ gh issue create --template "Bug Report"
```

Example 3 (unknown):
```unknown
# Create an issue interactively
~/Projects/my-project$ gh issue create
Creating issue in owner/repo
? Title My new issue
? Body [(e) to launch nano, enter to skip]
http://github.com/owner/repo/issues/1
~/Projects/my-project$
```

Example 4 (unknown):
```unknown
# Create an issue using flags
~/Projects/my-project$ gh issue create --title "Issue title" --body "Issue body"
http://github.com/owner/repo/issues/1
~/Projects/my-project$
```

---

## gh repo license list

**URL:** https://cli.github.com/manual/gh_repo_license_list

**Contents:**
- gh repo license list
  - ALIASES
  - See also

List common repository licenses.

For even more licenses, visit https://choosealicense.com/appendix

**Examples:**

Example 1 (unknown):
```unknown
gh repo license list
```

---

## gh attestation download

**URL:** https://cli.github.com/manual/gh_attestation_download

**Contents:**
- gh attestation download
  - NOTE: This feature is currently in public preview, and subject to change.
  - Options
  - Examples
  - See also

Download attestations associated with an artifact for offline use.

The command requires either:

In addition, the command requires either:

The --repo flag value must match the name of the GitHub repository that the artifact is linked with.

The --owner flag value must match the name of the GitHub organization that the artifact's linked repository belongs to.

Any associated bundle(s) will be written to a file in the current directory named after the artifact's digest. For example, if the digest is "sha256:1234", the file will be named "sha256:1234.jsonl".

Colons are special characters on Windows and cannot be used in file names. To accommodate, a dash will be used to separate the algorithm from the digest in the attestations file name. For example, if the digest is "sha256:1234", the file will be named "sha256-1234.jsonl".

**Examples:**

Example 1 (unknown):
```unknown
gh attestation download [<file-path> | oci://<image-uri>] [--owner | --repo] [flags]
```

Example 2 (bash):
```bash
# Download attestations for a local artifact linked with an organization
$ gh attestation download example.bin -o github

# Download attestations for a local artifact linked with a repository
$ gh attestation download example.bin -R github/example

# Download attestations for an OCI image linked with an organization
$ gh attestation download oci://example.com/foo/bar:latest -o github
```

---

## gh repo unarchive

**URL:** https://cli.github.com/manual/gh_repo_unarchive

**Contents:**
- gh repo unarchive
  - Options
  - See also

Unarchive a GitHub repository.

With no argument, unarchives the current repository.

**Examples:**

Example 1 (unknown):
```unknown
gh repo unarchive [<repository>] [flags]
```

---

## gh gist create

**URL:** https://cli.github.com/manual/gh_gist_create

**Contents:**
- gh gist create
  - Options
  - ALIASES
  - Examples
  - See also

Create a new GitHub gist with given contents.

Gists can be created from one or multiple files. Alternatively, pass - as filename to read from standard input.

By default, gists are secret; use --public to make publicly listed ones.

**Examples:**

Example 1 (unknown):
```unknown
gh gist create [<filename>... | <pattern>... | -] [flags]
```

Example 2 (bash):
```bash
# Publish file 'hello.py' as a public gist
$ gh gist create --public hello.py

# Create a gist with a description
$ gh gist create hello.py -d "my Hello-World program in Python"

# Create a gist containing several files
$ gh gist create hello.py world.py cool.txt

# Create a gist containing several files using patterns
$ gh gist create *.md *.txt artifact.*

# Read from standard input to create a gist
$ gh gist create -

# Create a gist from output piped from another command
$ cat cool.txt | gh gist create
```

---

## gh repo license view

**URL:** https://cli.github.com/manual/gh_repo_license_view

**Contents:**
- gh repo license view
  - Options
  - Examples
  - See also

View a specific repository license by license key or SPDX ID.

Run gh repo license list to see available commonly used licenses. For even more licenses, visit https://choosealicense.com/appendix.

**Examples:**

Example 1 (unknown):
```unknown
gh repo license view {<license-key> | <spdx-id>} [flags]
```

Example 2 (bash):
```bash
# View the MIT license from SPDX ID
$ gh repo license view MIT

# View the MIT license from license key
$ gh repo license view mit

# View the GNU AGPL-3.0 license from SPDX ID
$ gh repo license view AGPL-3.0

# View the GNU AGPL-3.0 license from license key
$ gh repo license view agpl-3.0

# Create a LICENSE.md with the MIT license
$ gh repo license view MIT > LICENSE.md
```

---

## gh repo autolink create

**URL:** https://cli.github.com/manual/gh_repo_autolink_create

**Contents:**
- gh repo autolink create
  - Options
  - Options inherited from parent commands
  - ALIASES
  - Examples
  - See also

Create a new autolink reference for a repository.

The keyPrefix argument specifies the prefix that will generate a link when it is appended by certain characters.

The urlTemplate argument specifies the target URL that will be generated when the keyPrefix is found, which must contain <num> variable for the reference number.

By default, autolinks are alphanumeric with --numeric flag used to create a numeric autolink.

The <num> variable behavior differs depending on whether the autolink is alphanumeric or numeric:

If the template contains multiple instances of <num>, only the first will be replaced.

**Examples:**

Example 1 (unknown):
```unknown
gh repo autolink create <keyPrefix> <urlTemplate> [flags]
```

Example 2 (bash):
```bash
# Create an alphanumeric autolink to example.com for the key prefix "TICKET-".
# Generates https://example.com/TICKET?query=123abc from "TICKET-123abc".
$ gh repo autolink create TICKET- "https://example.com/TICKET?query=<num>"

# Create a numeric autolink to example.com for the key prefix "STORY-".
# Generates https://example.com/STORY?id=123 from "STORY-123".
$ gh repo autolink create STORY- "https://example.com/STORY?id=<num>" --numeric
```

---

## gh repo fork

**URL:** https://cli.github.com/manual/gh_repo_fork

**Contents:**
- gh repo fork
  - Options
  - See also
  - In use
    - With no arguments
    - With arguments
    - Using flags

Create a fork of a repository.

With no argument, creates a fork of the current repository. Otherwise, forks the specified repository.

By default, the new fork is set to be your origin remote and any existing origin remote is renamed to upstream. To alter this behavior, you can set a name for the new fork's remote with --remote-name.

The upstream remote will be set as the default remote repository.

Additional git clone flags can be passed after --.

Inside a git repository, and without any arguments, we will automatically create a fork on GitHub on your account for your current directory. It will then prompt if you want to set an upstream remote.

If you pass a repository in OWNER/REPO format, `gh` will automatically create a fork on GitHub on your account and ask if you want to clone it. This works inside or outside of a git repository.

Use flags to skip prompts about adding a git remote for the fork, or about cloning the forked repository locally.

**Examples:**

Example 1 (unknown):
```unknown
gh repo fork [<repository>] [-- <gitflags>...] [flags]
```

Example 2 (unknown):
```unknown
# Create a fork for the current repository.
~/Projects/cli$ gh repo fork
- Forking cli/cli...
✓ Created fork user/cli
? Would you like to add a remote for the fork? Yes
✓ Renamed origin remote to upstream
✓ Added remote origin
~/Projects/cli$
```

Example 3 (unknown):
```unknown
# Create a fork for another repository.
~/Projects$ gh repo fork cli/cli
- Forking cli/cli...
✓ Created fork cli/cli
? Would you like to clone the fork? Yes
Cloning into 'cli'...
✓ Cloned fork
~/Projects$ cd cli
~/Projects/cli$
```

Example 4 (unknown):
```unknown
# Skipping remote prompts using flags
~/Projects/cli$ gh repo fork --remote=false
- Forking cli/cli...
✓ Created fork user/cli
~/Projects/cli$
```

---

## gh repo license

**URL:** https://cli.github.com/manual/gh_repo_license

**Contents:**
- gh repo license
  - Available commands
  - See also

Explore repository licenses

---

## gh label delete

**URL:** https://cli.github.com/manual/gh_label_delete

**Contents:**
- gh label delete
  - Options
  - Options inherited from parent commands
  - See also

Delete a label from a repository

**Examples:**

Example 1 (unknown):
```unknown
gh label delete <name> [flags]
```

---

## gh extension install

**URL:** https://cli.github.com/manual/gh_extension_install

**Contents:**
- gh extension install
  - Options
  - Examples
  - See also

Install a GitHub CLI extension from a GitHub or local repository.

For GitHub repositories, the repository argument can be specified in OWNER/REPO format or as a full repository URL. The URL format is useful when the repository is not hosted on github.com.

For remote repositories, the GitHub CLI first looks for the release artifacts assuming that it's a binary extension i.e. prebuilt binaries provided as part of the release. In the absence of a release, the repository itself is cloned assuming that it's a script extension i.e. prebuilt executable or script exists on its root.

The --pin flag may be used to specify a tag or commit for binary and script extensions respectively, the latest version is used otherwise.

For local repositories, often used while developing extensions, use . as the value of the repository argument. Note the following:

For the list of available extensions, see https://github.com/topics/gh-extension.

**Examples:**

Example 1 (unknown):
```unknown
gh extension install <repository> [flags]
```

Example 2 (bash):
```bash
# Install an extension from a remote repository hosted on GitHub
$ gh extension install owner/gh-extension

# Install an extension from a remote repository via full URL
$ gh extension install https://my.ghes.com/owner/gh-extension

# Install an extension from a local repository in the current working directory
$ gh extension install .
```

---

## gh repo edit

**URL:** https://cli.github.com/manual/gh_repo_edit

**Contents:**
- gh repo edit
  - Options
  - Examples
  - See also

Edit repository settings.

To toggle a setting off, use the --<flag>=false syntax.

Changing repository visibility can have unexpected consequences including but not limited to:

When the --visibility flag is used, --accept-visibility-change-consequences flag is required.

For information on all the potential consequences, see https://gh.io/setting-repository-visibility.

**Examples:**

Example 1 (unknown):
```unknown
gh repo edit [<repository>] [flags]
```

Example 2 (bash):
```bash
# Enable issues and wiki
$ gh repo edit --enable-issues --enable-wiki

# Disable projects
$ gh repo edit --enable-projects=false
```

---

## gh repo set-default

**URL:** https://cli.github.com/manual/gh_repo_set-default

**Contents:**
- gh repo set-default
  - NOTE: gh does not use the default repository for managing repository and environment secrets.
  - Options
  - Examples
  - See also

This command sets the default remote repository to use when querying the GitHub API for the locally cloned repository.

gh uses the default repository for things like:

**Examples:**

Example 1 (unknown):
```unknown
gh repo set-default [<repository>] [flags]
```

Example 2 (bash):
```bash
# Interactively select a default repository
$ gh repo set-default

# Set a repository explicitly
$ gh repo set-default owner/repo

# View the current default repository
$ gh repo set-default --view

# Show more repository options in the interactive picker
$ git remote add newrepo https://github.com/owner/repo
$ gh repo set-default
```

---

## gh ruleset view

**URL:** https://cli.github.com/manual/gh_ruleset_view

**Contents:**
- gh ruleset view
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

View information about a GitHub ruleset.

If no ID is provided, an interactive prompt will be used to choose the ruleset to view.

Use the --parents flag to control whether rulesets configured at higher levels that also apply to the provided repository or organization should be returned. The default is true.

**Examples:**

Example 1 (unknown):
```unknown
gh ruleset view [<ruleset-id>] [flags]
```

Example 2 (bash):
```bash
# Interactively choose a ruleset to view from all rulesets that apply to the current repository
$ gh ruleset view

# Interactively choose a ruleset to view from only rulesets configured in the current repository
$ gh ruleset view --no-parents

# View a ruleset configured in the current repository or any of its parents
$ gh ruleset view 43

# View a ruleset configured in a different repository or any of its parents
$ gh ruleset view 23 --repo owner/repo

# View an organization-level ruleset
$ gh ruleset view 23 --org my-org
```

---

## gh repo gitignore

**URL:** https://cli.github.com/manual/gh_repo_gitignore

**Contents:**
- gh repo gitignore
  - Available commands
  - See also

List and view available repository gitignore templates

---

## gh ruleset

**URL:** https://cli.github.com/manual/gh_ruleset

**Contents:**
- gh ruleset
  - Available commands
  - Options
  - ALIASES
  - Examples
  - See also

Repository rulesets are a way to define a set of rules that apply to a repository. These commands allow you to view information about them.

**Examples:**

Example 1 (bash):
```bash
$ gh ruleset list
$ gh ruleset view --repo OWNER/REPO --web
$ gh ruleset check branch-name
```

---

## gh pr view

**URL:** https://cli.github.com/manual/gh_pr_view

**Contents:**
- gh pr view
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also
  - In use
    - In terminal
    - In the browser
    - With no arguments

Display the title, body, and other information about a pull request.

Without an argument, the pull request that belongs to the current branch is displayed.

With --web flag, open the pull request in a web browser instead.

additions, assignees, author, autoMergeRequest, baseRefName, baseRefOid, body, changedFiles, closed, closedAt, closingIssuesReferences, comments, commits, createdAt, deletions, files, fullDatabaseId, headRefName, headRefOid, headRepository, headRepositoryOwner, id, isCrossRepository, isDraft, labels, latestReviews, maintainerCanModify, mergeCommit, mergeStateStatus, mergeable, mergedAt, mergedBy, milestone, number, potentialMergeCommit, projectCards, projectItems, reactionGroups, reviewDecision, reviewRequests, reviews, state, statusCheckRollup, title, updatedAt, url

By default, we will display items in the terminal.

Quickly open an item in the browser using --web or -w

We will display the pull request of the branch you're currently on.

**Examples:**

Example 1 (unknown):
```unknown
gh pr view [<number> | <url> | <branch>] [flags]
```

Example 2 (unknown):
```unknown
# Viewing a pull request in terminal
~/Projects/my-project$ gh pr view 21
Pull request title
opened by user. 0 comments. (label)

  Pull request body

View this pull request on GitHub: https://github.com/owner/repo/pull/21
~/Projects/my-project$
```

Example 3 (unknown):
```unknown
# Viewing a pull request in the browser
~/Projects/my-project$ gh pr view 21 --web
Opening https://github.com/owner/repo/pull/21 in your browser.
~/Projects/my-project$
```

Example 4 (unknown):
```unknown
# Viewing the pull request of the branch you're on
~/Projects/my-project$ gh pr view
Pull request title
opened by user. 0 comments. (label)

  Pull request body

View this pull request on GitHub: https://github.com/owner/repo/pull/21
~/Projects/my-project$
```

---

## gh secret

**URL:** https://cli.github.com/manual/gh_secret

**Contents:**
- gh secret
  - Available commands
  - Options
  - See also

Secrets can be set at the repository, or organization level for use in GitHub Actions or Dependabot. User, organization, and repository secrets can be set for use in GitHub Codespaces. Environment secrets can be set for use in GitHub Actions. Run gh help secret set to learn how to get started.

---

## gh project field-create

**URL:** https://cli.github.com/manual/gh_project_field-create

**Contents:**
- gh project field-create
  - Options
  - Examples
  - See also

Create a field in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project field-create [<number>] [flags]
```

Example 2 (bash):
```bash
# Create a field in the current user's project "1"
$ gh project field-create 1 --owner "@me" --name "new field" --data-type "text"

# Create a field with three options to select from for owner monalisa
$ gh project field-create 1 --owner monalisa --name "new field" --data-type "SINGLE_SELECT" --single-select-options "one,two,three"
```

---

## GitHub CLI usage examples

**URL:** https://cli.github.com/manual/examples

**Contents:**
- GitHub CLI usage examples
  - Checking out a pull request locally
    - Using pull request number
    - Using other selectors
  - Cloning a repository
    - Using OWNER/REPO syntax
    - Using other selectors
  - Creating issues and pull requests
    - Interactively
    - With flags

You can check out any pull request, including from forks, in a repository using its pull request number

You can also use URLs and branch names to checkout pull requests.

You can clone any repository using OWNER/REPO syntax.

You can also use GitHub URLs to clone repositories.

This command will automatically create a fork for you if you're in a repository that you don't have permission to push to.

Inside a git repository, and without any arguments, we will automatically create a fork on GitHub on your account for your current directory. It will then prompt if you want to set an upstream remote.

If you pass a repository in OWNER/REPO format, `gh` will automatically create a fork on GitHub on your account and ask if you want to clone it. This works inside or outside of a git repository.

Use flags to skip prompts about adding a git remote for the fork, or about cloning the forked repository locally.

You will see the most recent 30 open items.

You can use flags to filter the list for your specific use cases.

By default, we will display items in the terminal.

Quickly open an item in the browser using --web or -w

We will display the pull request of the branch you're currently on.

We will display the repository you're currently in.

**Examples:**

Example 1 (unknown):
```unknown
// Checking out a pull request locally
~/Projects/my-project$ gh pr checkout 12
remote: Enumerating objects: 66, done.
remote: Counting objects: 100% (66/66), done.
remote: Total 83 (delta 66), reused 66 (delta 66), pack-reused 17
Unpacking objects: 100% (83/83), done.
From https://github.com/owner/repo
 * [new ref]             refs/pull/8896/head -> patch-2
M       README.md
Switched to branch 'patch-2'

~/Projects/my-project$
```

Example 2 (unknown):
```unknown
// Checking out a pull request locally
~/Projects/my-project$ gh pr checkout branch-name
Switched to branch 'branch-name'
Your branch is up to date with 'origin/branch-name'.
Already up to date.

~/Projects/my-project$
```

Example 3 (unknown):
```unknown
# Cloning a repository
~/Projects$ gh repo clone cli/cli
Cloning into 'cli'...
~/Projects$ cd cli
~/Projects/cli$
```

Example 4 (unknown):
```unknown
# Cloning a repository
~/Projects/my-project$ gh repo clone https://github.com/cli/cli
Cloning into 'cli'...
remote: Enumerating objects: 99, done.
remote: Counting objects: 100% (99/99), done.
remote: Compressing objects: 100% (76/76), done.
remote: Total 21160 (delta 49), reused 35 (delta 18), pack-reused 21061
Receiving objects: 100% (21160/21160), 57.93 MiB | 10.82 MiB/s, done.
Resolving deltas: 100% (16051/16051), done.

~/Projects/my-project$
```

---

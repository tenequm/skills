# Gh-Cli - Issues

**Pages:** 15

---

## gh issue lock

**URL:** https://cli.github.com/manual/gh_issue_lock

**Contents:**
- gh issue lock
  - Options
  - Options inherited from parent commands
  - See also

Lock issue conversation

**Examples:**

Example 1 (unknown):
```unknown
gh issue lock {<number> | <url>} [flags]
```

---

## gh issue delete

**URL:** https://cli.github.com/manual/gh_issue_delete

**Contents:**
- gh issue delete
  - Options
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh issue delete {<number> | <url>} [flags]
```

---

## gh label

**URL:** https://cli.github.com/manual/gh_label

**Contents:**
- gh label
  - Available commands
  - Options
  - See also

Work with GitHub labels.

---

## gh issue develop

**URL:** https://cli.github.com/manual/gh_issue_develop

**Contents:**
- gh issue develop
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Manage linked branches for an issue.

When using the --base flag, the new development branch will be created from the specified remote branch. The new branch will be configured as the base branch for pull requests created using gh pr create.

**Examples:**

Example 1 (unknown):
```unknown
gh issue develop {<number> | <url>} [flags]
```

Example 2 (bash):
```bash
# List branches for issue 123
$ gh issue develop --list 123

# List branches for issue 123 in repo cli/cli
$ gh issue develop --list --repo cli/cli 123

# Create a branch for issue 123 based on the my-feature branch
$ gh issue develop 123 --base my-feature

# Create a branch for issue 123 and checkout it out
$ gh issue develop 123 --checkout

# Create a branch in repo monalisa/cli for issue 123 in repo cli/cli
$ gh issue develop 123 --repo cli/cli --branch-repo monalisa/cli
```

---

## gh label edit

**URL:** https://cli.github.com/manual/gh_label_edit

**Contents:**
- gh label edit
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Update a label on GitHub.

A label can be renamed using the --name flag.

The label color needs to be 6 character hex value.

**Examples:**

Example 1 (unknown):
```unknown
gh label edit <name> [flags]
```

Example 2 (bash):
```bash
# Update the color of the bug label
$ gh label edit bug --color FF0000

# Rename and edit the description of the bug label
$ gh label edit bug --name big-bug --description "Bigger than normal bug"
```

---

## gh auth status

**URL:** https://cli.github.com/manual/gh_auth_status

**Contents:**
- gh auth status
  - Options
  - JSON Fields
  - Examples
  - See also

Display active account and authentication state on each known GitHub host.

For each host, the authentication state of each known account is tested and any issues are included in the output. Each host section will indicate the active account, which will be used when targeting that host.

If an account on any host (or only the one given via --hostname) has authentication issues, the command will exit with 1 and output to stderr. Note that when using the --json option, the command will always exit with zero regardless of any authentication issues, unless there is a fatal error.

To change the active account for a host, see gh auth switch.

**Examples:**

Example 1 (unknown):
```unknown
gh auth status [flags]
```

Example 2 (bash):
```bash
# Display authentication status for all accounts on all hosts
$ gh auth status

# Display authentication status for the active account on a specific host
$ gh auth status --active --hostname github.example.com

# Display tokens in plain text
$ gh auth status --show-token

# Format authentication status as JSON
$ gh auth status --json hosts

# Include plain text token in JSON output
$ gh auth status --json hosts --show-token

# Format hosts as a flat JSON array
$ gh auth status --json hosts --jq '.hosts | add'
```

---

## gh issue unlock

**URL:** https://cli.github.com/manual/gh_issue_unlock

**Contents:**
- gh issue unlock
  - Options inherited from parent commands
  - See also

Unlock issue conversation

**Examples:**

Example 1 (unknown):
```unknown
gh issue unlock {<number> | <url>}
```

---

## gh alias set

**URL:** https://cli.github.com/manual/gh_alias_set

**Contents:**
- gh alias set
  - Options
  - Examples
  - See also

Define a word that will expand to a full gh command when invoked.

The expansion may specify additional arguments and flags. If the expansion includes positional placeholders such as $1, extra arguments that follow the alias will be inserted appropriately. Otherwise, extra arguments will be appended to the expanded command.

Use - as expansion argument to read the expansion string from standard input. This is useful to avoid quoting issues when defining expansions.

If the expansion starts with ! or if --shell was given, the expansion is a shell expression that will be evaluated through the sh interpreter when the alias is invoked. This allows for chaining multiple commands via piping and redirection.

**Examples:**

Example 1 (unknown):
```unknown
gh alias set <alias> <expansion> [flags]
```

Example 2 (bash):
```bash
# Note: Command Prompt on Windows requires using double quotes for arguments
$ gh alias set pv 'pr view'
$ gh pv -w 123  #=> gh pr view -w 123

$ gh alias set bugs 'issue list --label=bugs'
$ gh bugs

$ gh alias set homework 'issue list --assignee @me'
$ gh homework

$ gh alias set 'issue mine' 'issue list --mention @me'
$ gh issue mine

$ gh alias set epicsBy 'issue list --author="$1" --label="epic"'
$ gh epicsBy vilmibm  #=> gh issue list --author="vilmibm" --label="epic"

$ gh alias set --shell igrep 'gh issue list --label="$1" | grep "$2"'
$ gh igrep epic foo  #=> gh issue list --label="epic" | grep "foo"
```

---

## gh project item-edit

**URL:** https://cli.github.com/manual/gh_project_item-edit

**Contents:**
- gh project item-edit
  - Options
  - Examples
  - See also

Edit either a draft issue or a project item. Both usages require the ID of the item to edit.

For non-draft issues, the ID of the project is also required, and only a single field value can be updated per invocation.

Remove project item field value using --clear flag.

**Examples:**

Example 1 (unknown):
```unknown
gh project item-edit [flags]
```

Example 2 (bash):
```bash
# Edit an item's text field value
$ gh project item-edit --id <item-id> --field-id <field-id> --project-id <project-id> --text "new text"

# Clear an item's field value
$ gh project item-edit --id <item-id> --field-id <field-id> --project-id <project-id> --clear
```

---

## gh issue status

**URL:** https://cli.github.com/manual/gh_issue_status

**Contents:**
- gh issue status
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also
  - In use

Show status of relevant issues

assignees, author, body, closed, closedAt, closedByPullRequestsReferences, comments, createdAt, id, isPinned, labels, milestone, number, projectCards, projectItems, reactionGroups, state, stateReason, title, updatedAt, url

**Examples:**

Example 1 (unknown):
```unknown
gh issue status [flags]
```

Example 2 (unknown):
```unknown
# Viewing issues relevant to you
~/Projects/my-project$ gh issue status
Issues assigned to you
  #8509 [Fork] Improve how Desktop handles forks  (epic:fork, meta)

Issues mentioning you
  #8938 [Fork] Add create fork flow entry point at commit warning  (epic:fork)
  #8509 [Fork] Improve how Desktop handles forks  (epic:fork, meta)

Issues opened by you
  #8936 [Fork] Hide PR number badges on branches that have an upstream PR  (epic:fork)
  #6386 Improve no editor detected state on conflicts modal  (enhancement)

~/Projects/my-project$
```

---

## gh issue

**URL:** https://cli.github.com/manual/gh_issue

**Contents:**
- gh issue
  - General commands
  - Targeted commands
  - Options
  - Examples
  - See also

Work with GitHub issues.

**Examples:**

Example 1 (bash):
```bash
$ gh issue list
$ gh issue create --label bug
$ gh issue view 123 --web
```

---

## gh issue view

**URL:** https://cli.github.com/manual/gh_issue_view

**Contents:**
- gh issue view
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also
  - In use
    - In terminal
    - In the browser

Display the title, body, and other information about an issue.

With --web flag, open the issue in a web browser instead.

assignees, author, body, closed, closedAt, closedByPullRequestsReferences, comments, createdAt, id, isPinned, labels, milestone, number, projectCards, projectItems, reactionGroups, state, stateReason, title, updatedAt, url

By default, we will display items in the terminal.

Quickly open an item in the browser using --web or -w

**Examples:**

Example 1 (unknown):
```unknown
gh issue view {<number> | <url>} [flags]
```

Example 2 (unknown):
```unknown
# Viewing an issue in terminal
~/Projects/my-project$ gh issue view 21
Issue title
opened by user. 0 comments. (label)

  Issue body

View this issue on GitHub: https://github.com/owner/repo/issues/21
~/Projects/my-project$
```

Example 3 (unknown):
```unknown
# Viewing an issue in the browser
~/Projects/my-project$ gh issue view 21 --web
Opening https://github.com/owner/repo/issues/21 in your browser.
~/Projects/my-project$
```

---

## gh issue reopen

**URL:** https://cli.github.com/manual/gh_issue_reopen

**Contents:**
- gh issue reopen
  - Options
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh issue reopen {<number> | <url>} [flags]
```

---

## gh issue comment

**URL:** https://cli.github.com/manual/gh_issue_comment

**Contents:**
- gh issue comment
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Add a comment to a GitHub issue.

Without the body text supplied through flags, the command will interactively prompt for the comment text.

**Examples:**

Example 1 (unknown):
```unknown
gh issue comment {<number> | <url>} [flags]
```

Example 2 (bash):
```bash
$ gh issue comment 12 --body "Hi from GitHub CLI"
```

---

## gh issue close

**URL:** https://cli.github.com/manual/gh_issue_close

**Contents:**
- gh issue close
  - Options
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh issue close {<number> | <url>} [flags]
```

---

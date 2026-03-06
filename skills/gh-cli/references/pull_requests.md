# Gh-Cli - Pull Requests

**Pages:** 31

---

## gh project view

**URL:** https://cli.github.com/manual/gh_project_view

**Contents:**
- gh project view
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project view [<number>] [flags]
```

Example 2 (bash):
```bash
# View the current user's project "1"
$ gh project view 1

# Open user monalisa's project "1" in the browser
$ gh project view 1 --owner monalisa --web
```

---

## gh pr merge

**URL:** https://cli.github.com/manual/gh_pr_merge

**Contents:**
- gh pr merge
  - Options
  - Options inherited from parent commands
  - See also

Merge a pull request on GitHub.

Without an argument, the pull request that belongs to the current branch is selected.

When targeting a branch that requires a merge queue, no merge strategy is required. If required checks have not yet passed, auto-merge will be enabled. If required checks have passed, the pull request will be added to the merge queue. To bypass a merge queue and merge directly, pass the --admin flag.

**Examples:**

Example 1 (unknown):
```unknown
gh pr merge [<number> | <url> | <branch>] [flags]
```

---

## gh project copy

**URL:** https://cli.github.com/manual/gh_project_copy

**Contents:**
- gh project copy
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project copy [<number>] [flags]
```

Example 2 (bash):
```bash
# Copy project "1" owned by monalisa to github
$ gh project copy 1 --source-owner monalisa --target-owner github --title "a new project"
```

---

## gh project item-add

**URL:** https://cli.github.com/manual/gh_project_item-add

**Contents:**
- gh project item-add
  - Options
  - Examples
  - See also

Add a pull request or an issue to a project

**Examples:**

Example 1 (unknown):
```unknown
gh project item-add [<number>] [flags]
```

Example 2 (bash):
```bash
# Add an item to monalisa's project "1"
$ gh project item-add 1 --owner monalisa --url https://github.com/monalisa/myproject/issues/23
```

---

## gh preview prompter

**URL:** https://cli.github.com/manual/gh_preview_prompter

**Contents:**
- gh preview prompter
  - See also

Execute a test program to preview the prompter. Without an argument, all prompts will be run.

Available prompt types:

**Examples:**

Example 1 (unknown):
```unknown
gh preview prompter [prompt type]
```

---

## gh pr update-branch

**URL:** https://cli.github.com/manual/gh_pr_update-branch

**Contents:**
- gh pr update-branch
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Update a pull request branch with latest changes of the base branch.

Without an argument, the pull request that belongs to the current branch is selected.

The default behavior is to update with a merge commit (i.e., merging the base branch into the PR's branch). To reconcile the changes with rebasing on top of the base branch, the --rebase option should be provided.

**Examples:**

Example 1 (unknown):
```unknown
gh pr update-branch [<number> | <url> | <branch>] [flags]
```

Example 2 (bash):
```bash
$ gh pr update-branch 23
$ gh pr update-branch 23 --rebase
$ gh pr update-branch 23 --repo owner/repo
```

---

## gh agent-task list

**URL:** https://cli.github.com/manual/gh_agent-task_list

**Contents:**
- gh agent-task list
  - Options
  - See also

List agent tasks (preview)

**Examples:**

Example 1 (unknown):
```unknown
gh agent-task list [flags]
```

---

## gh pr edit

**URL:** https://cli.github.com/manual/gh_pr_edit

**Contents:**
- gh pr edit
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Without an argument, the pull request that belongs to the current branch is selected.

Editing a pull request's projects requires authorization with the project scope. To authorize, run gh auth refresh -s project.

The --add-assignee and --remove-assignee flags both support the following special values:

The --add-reviewer and --remove-reviewer flags do not support these special values.

**Examples:**

Example 1 (unknown):
```unknown
gh pr edit [<number> | <url> | <branch>] [flags]
```

Example 2 (bash):
```bash
$ gh pr edit 23 --title "I found a bug" --body "Nothing works"
$ gh pr edit 23 --add-label "bug,help wanted" --remove-label "core"
$ gh pr edit 23 --add-reviewer monalisa,hubot  --remove-reviewer myorg/team-name
$ gh pr edit 23 --add-assignee "@me" --remove-assignee monalisa,hubot
$ gh pr edit 23 --add-assignee "@copilot"
$ gh pr edit 23 --add-project "Roadmap" --remove-project v1,v2
$ gh pr edit 23 --milestone "Version 1"
$ gh pr edit 23 --remove-milestone
```

---

## gh project mark-template

**URL:** https://cli.github.com/manual/gh_project_mark-template

**Contents:**
- gh project mark-template
  - Options
  - Examples
  - See also

Mark a project as a template

**Examples:**

Example 1 (unknown):
```unknown
gh project mark-template [<number>] [flags]
```

Example 2 (bash):
```bash
# Mark the github org's project "1" as a template
$ gh project mark-template 1 --owner "github"

# Unmark the github org's project "1" as a template
$ gh project mark-template 1 --owner "github" --undo
```

---

## gh pr review

**URL:** https://cli.github.com/manual/gh_pr_review

**Contents:**
- gh pr review
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Add a review to a pull request.

Without an argument, the pull request that belongs to the current branch is reviewed.

**Examples:**

Example 1 (unknown):
```unknown
gh pr review [<number> | <url> | <branch>] [flags]
```

Example 2 (bash):
```bash
# Approve the pull request of the current branch
$ gh pr review --approve

# Leave a review comment for the current branch
$ gh pr review --comment -b "interesting"

# Add a review for a specific pull request
$ gh pr review 123

# Request changes on a specific pull request
$ gh pr review 123 -r -b "needs more ASCII art"
```

---

## gh preview

**URL:** https://cli.github.com/manual/gh_preview

**Contents:**
- gh preview
  - Available commands
  - See also

Preview commands are for testing, demonstrative, and development purposes only. They should be considered unstable and can change at any time.

---

## gh pr close

**URL:** https://cli.github.com/manual/gh_pr_close

**Contents:**
- gh pr close
  - Options
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh pr close {<number> | <url> | <branch>} [flags]
```

---

## gh project delete

**URL:** https://cli.github.com/manual/gh_project_delete

**Contents:**
- gh project delete
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project delete [<number>] [flags]
```

Example 2 (bash):
```bash
# Delete the current user's project "1"
$ gh project delete 1 --owner "@me"
```

---

## gh pr lock

**URL:** https://cli.github.com/manual/gh_pr_lock

**Contents:**
- gh pr lock
  - Options
  - Options inherited from parent commands
  - See also

Lock pull request conversation

**Examples:**

Example 1 (unknown):
```unknown
gh pr lock {<number> | <url>} [flags]
```

---

## gh agent-task

**URL:** https://cli.github.com/manual/gh_agent-task

**Contents:**
- gh agent-task
  - Available commands
  - ALIASES
  - Examples
  - See also

Working with agent tasks in the GitHub CLI is in preview and subject to change without notice.

gh agent, gh agents, gh agent-tasks

**Examples:**

Example 1 (unknown):
```unknown
gh agent-task <command>
```

Example 2 (bash):
```bash
# List your most recent agent tasks
$ gh agent-task list

# Create a new agent task on the current repository
$ gh agent-task create "Improve the performance of the data processing pipeline"

# View details about agent tasks associated with a pull request
$ gh agent-task view 123

# View details about a specific agent task
$ gh agent-task view 12345abc-12345-12345-12345-12345abc
```

---

## gh pr comment

**URL:** https://cli.github.com/manual/gh_pr_comment

**Contents:**
- gh pr comment
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Add a comment to a GitHub pull request.

Without the body text supplied through flags, the command will interactively prompt for the comment text.

**Examples:**

Example 1 (unknown):
```unknown
gh pr comment [<number> | <url> | <branch>] [flags]
```

Example 2 (bash):
```bash
$ gh pr comment 13 --body "Hi from GitHub CLI"
```

---

## gh project item-archive

**URL:** https://cli.github.com/manual/gh_project_item-archive

**Contents:**
- gh project item-archive
  - Options
  - Examples
  - See also

Archive an item in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project item-archive [<number>] [flags]
```

Example 2 (bash):
```bash
# Archive an item in the current user's project "1"
$ gh project item-archive 1 --owner "@me" --id <item-ID>
```

---

## gh project item-delete

**URL:** https://cli.github.com/manual/gh_project_item-delete

**Contents:**
- gh project item-delete
  - Options
  - Examples
  - See also

Delete an item from a project by ID

**Examples:**

Example 1 (unknown):
```unknown
gh project item-delete [<number>] [flags]
```

Example 2 (bash):
```bash
# Delete an item in the current user's project "1"
$ gh project item-delete 1 --owner "@me" --id <item-id>
```

---

## gh project close

**URL:** https://cli.github.com/manual/gh_project_close

**Contents:**
- gh project close
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project close [<number>] [flags]
```

Example 2 (bash):
```bash
# Close project "1" owned by monalisa
$ gh project close 1 --owner monalisa

# Reopen closed project "1" owned by github
$ gh project close 1 --owner github --undo
```

---

## gh project field-list

**URL:** https://cli.github.com/manual/gh_project_field-list

**Contents:**
- gh project field-list
  - Options
  - Examples
  - See also

List the fields in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project field-list [<number>] [flags]
```

Example 2 (bash):
```bash
# List fields in the current user's project "1"
$ gh project field-list 1 --owner "@me"
```

---

## gh project edit

**URL:** https://cli.github.com/manual/gh_project_edit

**Contents:**
- gh project edit
  - Options
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh project edit [<number>] [flags]
```

Example 2 (bash):
```bash
# Edit the title of monalisa's project "1"
$ gh project edit 1 --owner monalisa --title "New title"
```

---

## gh project item-list

**URL:** https://cli.github.com/manual/gh_project_item-list

**Contents:**
- gh project item-list
  - Options
  - Examples
  - See also

List the items in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project item-list [<number>] [flags]
```

Example 2 (bash):
```bash
# List the items in the current users's project "1"
$ gh project item-list 1 --owner "@me"
```

---

## gh pr diff

**URL:** https://cli.github.com/manual/gh_pr_diff

**Contents:**
- gh pr diff
  - Options
  - Options inherited from parent commands
  - See also

View changes in a pull request.

Without an argument, the pull request that belongs to the current branch is selected.

With --web flag, open the pull request diff in a web browser instead.

**Examples:**

Example 1 (unknown):
```unknown
gh pr diff [<number> | <url> | <branch>] [flags]
```

---

## gh project list

**URL:** https://cli.github.com/manual/gh_project_list

**Contents:**
- gh project list
  - Options
  - ALIASES
  - Examples
  - See also

List the projects for an owner

**Examples:**

Example 1 (unknown):
```unknown
gh project list [flags]
```

Example 2 (bash):
```bash
# List the current user's projects
$ gh project list

# List the projects for org github including closed projects
$ gh project list --owner github --closed
```

---

## gh project

**URL:** https://cli.github.com/manual/gh_project

**Contents:**
- gh project
  - Available commands
  - Examples
  - See also

Work with GitHub Projects.

The minimum required scope for the token is: project. You can verify your token scope by running gh auth status and add the project scope by running gh auth refresh -s project.

**Examples:**

Example 1 (bash):
```bash
$ gh project create --owner monalisa --title "Roadmap"
$ gh project view 1 --owner cli --web
$ gh project field-list 1 --owner cli
$ gh project item-list 1 --owner cli
```

---

## gh pr unlock

**URL:** https://cli.github.com/manual/gh_pr_unlock

**Contents:**
- gh pr unlock
  - Options inherited from parent commands
  - See also

Unlock pull request conversation

**Examples:**

Example 1 (unknown):
```unknown
gh pr unlock {<number> | <url>}
```

---

## gh pr reopen

**URL:** https://cli.github.com/manual/gh_pr_reopen

**Contents:**
- gh pr reopen
  - Options
  - Options inherited from parent commands
  - See also

Reopen a pull request

**Examples:**

Example 1 (unknown):
```unknown
gh pr reopen {<number> | <url> | <branch>} [flags]
```

---

## gh project field-delete

**URL:** https://cli.github.com/manual/gh_project_field-delete

**Contents:**
- gh project field-delete
  - Options
  - See also

Delete a field in a project

**Examples:**

Example 1 (unknown):
```unknown
gh project field-delete [flags]
```

---

## gh pr

**URL:** https://cli.github.com/manual/gh_pr

**Contents:**
- gh pr
  - General commands
  - Targeted commands
  - Options
  - Examples
  - See also

Work with GitHub pull requests.

**Examples:**

Example 1 (bash):
```bash
$ gh pr checkout 353
$ gh pr create --fill
$ gh pr view --web
```

---

## gh pr checks

**URL:** https://cli.github.com/manual/gh_pr_checks

**Contents:**
- gh pr checks
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - See also

Show CI status for a single pull request.

Without an argument, the pull request that belongs to the current branch is selected.

When the --json flag is used, it includes a bucket field, which categorizes the state field into pass, fail, pending, skipping, or cancel.

Additional exit codes: 8: Checks pending

bucket, completedAt, description, event, link, name, startedAt, state, workflow

**Examples:**

Example 1 (unknown):
```unknown
gh pr checks [<number> | <url> | <branch>] [flags]
```

---

## gh pr ready

**URL:** https://cli.github.com/manual/gh_pr_ready

**Contents:**
- gh pr ready
  - Options
  - Options inherited from parent commands
  - See also

Mark a pull request as ready for review.

Without an argument, the pull request that belongs to the current branch is marked as ready.

If supported by your plan, convert to draft with --undo

**Examples:**

Example 1 (unknown):
```unknown
gh pr ready [<number> | <url> | <branch>] [flags]
```

---

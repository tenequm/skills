# Gh-Cli - Search

**Pages:** 7

---

## gh search prs

**URL:** https://cli.github.com/manual/gh_search_prs

**Contents:**
- gh search prs
  - Options
  - JSON Fields
  - Examples
  - See also

Search for pull requests on GitHub.

The command supports constructing queries using the GitHub search syntax, using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at: https://docs.github.com/search-github/searching-on-github/searching-issues-and-pull-requests

On supported GitHub hosts, advanced issue search syntax can be used in the --search query. For more information about advanced issue search, see: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests#building-advanced-filters-for-issues

For more information on handling search queries containing a hyphen, run gh search --help.

assignees, author, authorAssociation, body, closedAt, commentsCount, createdAt, id, isDraft, isLocked, isPullRequest, labels, number, repository, state, title, updatedAt, url

**Examples:**

Example 1 (unknown):
```unknown
gh search prs [<query>] [flags]
```

Example 2 (bash):
```bash
# Search pull requests matching set of keywords "fix" and "bug"
$ gh search prs fix bug

# Search draft pull requests in cli repository
$ gh search prs --repo=cli/cli --draft

# Search open pull requests requesting your review
$ gh search prs --review-requested=@me --state=open

# Search merged pull requests assigned to yourself
$ gh search prs --assignee=@me --merged

# Search pull requests with numerous reactions
$ gh search prs --reactions=">100"

# Search pull requests without label "bug"
$ gh search prs -- -label:bug

# Search pull requests only from un-archived repositories (default is all repositories)
$ gh search prs --owner github --archived=false
```

---

## gh search issues

**URL:** https://cli.github.com/manual/gh_search_issues

**Contents:**
- gh search issues
  - Options
  - JSON Fields
  - Examples
  - See also

Search for issues on GitHub.

The command supports constructing queries using the GitHub search syntax, using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at: https://docs.github.com/search-github/searching-on-github/searching-issues-and-pull-requests

On supported GitHub hosts, advanced issue search syntax can be used in the --search query. For more information about advanced issue search, see: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/filtering-and-searching-issues-and-pull-requests#building-advanced-filters-for-issues

For more information on handling search queries containing a hyphen, run gh search --help.

assignees, author, authorAssociation, body, closedAt, commentsCount, createdAt, id, isLocked, isPullRequest, labels, number, repository, state, title, updatedAt, url

**Examples:**

Example 1 (unknown):
```unknown
gh search issues [<query>] [flags]
```

Example 2 (bash):
```bash
# Search issues matching set of keywords "readme" and "typo"
$ gh search issues readme typo

# Search issues matching phrase "broken feature"
$ gh search issues "broken feature"

# Search issues and pull requests in cli organization
$ gh search issues --include-prs --owner=cli

# Search open issues assigned to yourself
$ gh search issues --assignee=@me --state=open

# Search issues with numerous comments
$ gh search issues --comments=">100"

# Search issues without label "bug"
$ gh search issues -- -label:bug

# Search issues only from un-archived repositories (default is all repositories)
$ gh search issues --owner github --archived=false
```

---

## gh search code

**URL:** https://cli.github.com/manual/gh_search_code

**Contents:**
- gh search code
  - Options
  - JSON Fields
  - Examples
  - See also

Search within code in GitHub repositories.

The search syntax is documented at: https://docs.github.com/search-github/searching-on-github/searching-code

Note that these search results are powered by what is now a legacy GitHub code search engine. The results might not match what is seen on github.com, and new features like regex search are not yet available via the GitHub API.

For more information on handling search queries containing a hyphen, run gh search --help.

path, repository, sha, textMatches, url

**Examples:**

Example 1 (unknown):
```unknown
gh search code <query> [flags]
```

Example 2 (bash):
```bash
# Search code matching "react" and "lifecycle"
$ gh search code react lifecycle

# Search code matching "error handling"
$ gh search code "error handling"

# Search code matching "deque" in Python files
$ gh search code deque --language=python

# Search code matching "cli" in repositories owned by microsoft organization
$ gh search code cli --owner=microsoft

# Search code matching "panic" in the GitHub CLI repository
$ gh search code panic --repo cli/cli

# Search code matching keyword "lint" in package.json files
$ gh search code lint --filename package.json
```

---

## gh search commits

**URL:** https://cli.github.com/manual/gh_search_commits

**Contents:**
- gh search commits
  - Options
  - JSON Fields
  - Examples
  - See also

Search for commits on GitHub.

The command supports constructing queries using the GitHub search syntax, using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at: https://docs.github.com/search-github/searching-on-github/searching-commits

For more information on handling search queries containing a hyphen, run gh search --help.

author, commit, committer, id, parents, repository, sha, url

**Examples:**

Example 1 (unknown):
```unknown
gh search commits [<query>] [flags]
```

Example 2 (bash):
```bash
# Search commits matching set of keywords "readme" and "typo"
$ gh search commits readme typo

# Search commits matching phrase "bug fix"
$ gh search commits "bug fix"

# Search commits committed by user "monalisa"
$ gh search commits --committer=monalisa

# Search commits authored by users with name "Jane Doe"
$ gh search commits --author-name="Jane Doe"

# Search commits matching hash "8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3"
$ gh search commits --hash=8dd03144ffdc6c0d486d6b705f9c7fba871ee7c3

# Search commits authored before February 1st, 2022
$ gh search commits --author-date="<2022-02-01"
```

---

## gh extension search

**URL:** https://cli.github.com/manual/gh_extension_search

**Contents:**
- gh extension search
  - Options
  - JSON Fields
  - Examples
  - See also

Search for gh extensions.

With no arguments, this command prints out the first 30 extensions available to install sorted by number of stars. More extensions can be fetched by specifying a higher limit with the --limit flag.

When connected to a terminal, this command prints out three columns. The first has a ✓ if the extension is already installed locally. The second is the full name of the extension repository in OWNER/REPO format. The third is the extension's description.

When not connected to a terminal, the ✓ character is rendered as the word "installed" but otherwise the order and content of the columns are the same.

This command behaves similarly to gh search repos but does not support as many search qualifiers. For a finer grained search of extensions, try using:

and adding qualifiers as needed. See gh help search repos to learn more about repository search.

For listing just the extensions that are already installed locally, see:

createdAt, defaultBranch, description, forksCount, fullName, hasDownloads, hasIssues, hasPages, hasProjects, hasWiki, homepage, id, isArchived, isDisabled, isFork, isPrivate, language, license, name, openIssuesCount, owner, pushedAt, size, stargazersCount, updatedAt, url, visibility, watchersCount

**Examples:**

Example 1 (unknown):
```unknown
gh extension search [<query>] [flags]
```

Example 2 (unknown):
```unknown
gh search repos --topic "gh-extension"
```

Example 3 (unknown):
```unknown
gh ext list
```

Example 4 (bash):
```bash
# List the first 30 extensions sorted by star count, descending
$ gh ext search

# List more extensions
$ gh ext search --limit 300

# List extensions matching the term "branch"
$ gh ext search branch

# List extensions owned by organization "github"
$ gh ext search --owner github

# List extensions, sorting by recently updated, ascending
$ gh ext search --sort updated --order asc

# List extensions, filtering by license
$ gh ext search --license MIT

# Open search results in the browser
$ gh ext search -w
```

---

## gh search repos

**URL:** https://cli.github.com/manual/gh_search_repos

**Contents:**
- gh search repos
  - Options
  - JSON Fields
  - Examples
  - See also

Search for repositories on GitHub.

The command supports constructing queries using the GitHub search syntax, using the parameter and qualifier flags, or a combination of the two.

GitHub search syntax is documented at: https://docs.github.com/search-github/searching-on-github/searching-for-repositories

For more information on handling search queries containing a hyphen, run gh search --help.

createdAt, defaultBranch, description, forksCount, fullName, hasDownloads, hasIssues, hasPages, hasProjects, hasWiki, homepage, id, isArchived, isDisabled, isFork, isPrivate, language, license, name, openIssuesCount, owner, pushedAt, size, stargazersCount, updatedAt, url, visibility, watchersCount

**Examples:**

Example 1 (unknown):
```unknown
gh search repos [<query>] [flags]
```

Example 2 (bash):
```bash
# Search repositories matching set of keywords "cli" and "shell"
$ gh search repos cli shell

# Search repositories matching phrase "vim plugin"
$ gh search repos "vim plugin"

# Search repositories public repos in the microsoft organization
$ gh search repos --owner=microsoft --visibility=public

# Search repositories with a set of topics
$ gh search repos --topic=unix,terminal

# Search repositories by coding language and number of good first issues
$ gh search repos --language=go --good-first-issues=">=10"

# Search repositories without topic "linux"
$ gh search repos -- -topic:linux

# Search repositories excluding archived repositories
$ gh search repos --archived=false
```

---

## gh search

**URL:** https://cli.github.com/manual/gh_search

**Contents:**
- gh search
  - Available commands
  - See also

Search across all of GitHub.

Excluding search results that match a qualifier

In a browser, the GitHub search syntax supports excluding results that match a search qualifier by prefixing the qualifier with a hyphen. For example, to search for issues that do not have the label "bug", you would use -label:bug as a search qualifier.

gh supports this syntax in gh search as well, but it requires extra command line arguments to avoid the hyphen being interpreted as a command line flag because it begins with a hyphen.

On Unix-like systems, you can use the -- argument to indicate that the arguments that follow are not a flag, but rather a query string. For example:

$ gh search issues -- "my-search-query -label:bug"

On PowerShell, you must use both the --% argument and the -- argument to produce the same effect. For example:

$ gh --% search issues -- "my search query -label:bug"

See the following for more information:

---

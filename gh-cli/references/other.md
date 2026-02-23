# Gh-Cli - Other

**Pages:** 60

---

## gh config get

**URL:** https://cli.github.com/manual/gh_config_get

**Contents:**
- gh config get
  - Options
  - Examples
  - See also

Print the value of a given configuration key

**Examples:**

Example 1 (unknown):
```unknown
gh config get <key> [flags]
```

Example 2 (bash):
```bash
$ gh config get git_protocol
```

---

## gh environment

**URL:** https://cli.github.com/manual/gh_help_environment

**Contents:**
- gh environment
  - See also

GH_TOKEN, GITHUB_TOKEN (in order of precedence): an authentication token that will be used when a command targets either github.com or a subdomain of ghe.com. Setting this avoids being prompted to authenticate and takes precedence over previously stored credentials.

GH_ENTERPRISE_TOKEN, GITHUB_ENTERPRISE_TOKEN (in order of precedence): an authentication token that will be used when a command targets a GitHub Enterprise Server host.

GH_HOST: specify the GitHub hostname for commands where a hostname has not been provided, or cannot be inferred from the context of a local Git repository. If this host was previously authenticated with, the stored credentials will be used. Otherwise, setting GH_TOKEN or GH_ENTERPRISE_TOKEN is required, depending on the targeted host.

GH_REPO: specify the GitHub repository in the [HOST/]OWNER/REPO format for commands that otherwise operate on a local repository.

GH_EDITOR, GIT_EDITOR, VISUAL, EDITOR (in order of precedence): the editor tool to use for authoring text.

GH_BROWSER, BROWSER (in order of precedence): the web browser to use for opening links.

GH_DEBUG: set to a truthy value to enable verbose output on standard error. Set to api to additionally log details of HTTP traffic.

DEBUG (deprecated): set to 1, true, or yes to enable verbose output on standard error.

GH_PAGER, PAGER (in order of precedence): a terminal paging program to send standard output to, e.g. less.

GLAMOUR_STYLE: the style to use for rendering Markdown. See https://github.com/charmbracelet/glamour#styles

NO_COLOR: set to any value to avoid printing ANSI escape sequences for color output.

CLICOLOR: set to 0 to disable printing ANSI colors in output.

CLICOLOR_FORCE: set to a value other than 0 to keep ANSI colors in output even when the output is piped.

GH_COLOR_LABELS: set to any value to display labels using their RGB hex color codes in terminals that support truecolor.

GH_ACCESSIBLE_COLORS (preview): set to a truthy value to use customizable, 4-bit accessible colors.

GH_FORCE_TTY: set to any value to force terminal-style output even when the output is redirected. When the value is a number, it is interpreted as the number of columns available in the viewport. When the value is a percentage, it will be applied against the number of columns available in the current viewport.

GH_NO_UPDATE_NOTIFIER: set to any value to disable GitHub CLI update notifications. When any command is executed, gh checks for new versions once every 24 hours. If a newer version was found, an upgrade notice is displayed on standard error.

GH_NO_EXTENSION_UPDATE_NOTIFIER: set to any value to disable GitHub CLI extension update notifications. When an extension is executed, gh checks for new versions for the executed extension once every 24 hours. If a newer version was found, an upgrade notice is displayed on standard error.

GH_CONFIG_DIR: the directory where gh will store configuration files. If not specified, the default value will be one of the following paths (in order of precedence):

GH_PROMPT_DISABLED: set to any value to disable interactive prompting in the terminal.

GH_PATH: set the path to the gh executable, useful for when gh can not properly determine its own path such as in the cygwin terminal.

GH_MDWIDTH: default maximum width for markdown render wrapping. The max width of lines wrapped on the terminal will be taken as the lesser of the terminal width, this value, or 120 if not specified. This value is used, for example, with pr view subcommand.

GH_ACCESSIBLE_PROMPTER (preview): set to a truthy value to enable prompts that are more compatible with speech synthesis and braille screen readers.

GH_SPINNER_DISABLED: set to a truthy value to replace the spinner animation with a textual progress indicator.

---

## gh org

**URL:** https://cli.github.com/manual/gh_org

**Contents:**
- gh org
  - General commands
  - Examples
  - See also

Work with GitHub organizations.

**Examples:**

Example 1 (bash):
```bash
$ gh org list
```

---

## gh codespace

**URL:** https://cli.github.com/manual/gh_codespace

**Contents:**
- gh codespace
  - Available commands
  - ALIASES
  - See also

Connect to and manage codespaces

---

## gh gist

**URL:** https://cli.github.com/manual/gh_gist

**Contents:**
- gh gist
  - Available commands
  - See also

Work with GitHub gists.

---

## gh alias list

**URL:** https://cli.github.com/manual/gh_alias_list

**Contents:**
- gh alias list
  - ALIASES
  - See also

This command prints out all of the aliases gh is configured to use.

**Examples:**

Example 1 (unknown):
```unknown
gh alias list
```

---

## gh cache

**URL:** https://cli.github.com/manual/gh_cache

**Contents:**
- gh cache
  - Available commands
  - Options
  - Examples
  - See also

Work with GitHub Actions caches.

**Examples:**

Example 1 (bash):
```bash
$ gh cache list
$ gh cache delete --all
```

---

## gh codespace ports forward

**URL:** https://cli.github.com/manual/gh_codespace_ports_forward

**Contents:**
- gh codespace ports forward
  - Options inherited from parent commands
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh codespace ports forward <remote-port>:<local-port>...
```

---

## gh codespace edit

**URL:** https://cli.github.com/manual/gh_codespace_edit

**Contents:**
- gh codespace edit
  - Options
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh codespace edit [flags]
```

---

## gh auth login

**URL:** https://cli.github.com/manual/gh_auth_login

**Contents:**
- gh auth login
  - Options
  - Examples
  - See also

Authenticate with a GitHub host.

The default hostname is github.com. This can be overridden using the --hostname flag.

The default authentication mode is a web-based browser flow. After completion, an authentication token will be stored securely in the system credential store. If a credential store is not found or there is an issue using it gh will fallback to writing the token to a plain text file. See gh auth status for its stored location.

Alternatively, use --with-token to pass in a personal access token (classic) on standard input. The minimum required scopes for the token are: repo, read:org, and gist. Take care when passing a fine-grained personal access token to --with-token as the inherent scoping to certain resources may cause confusing behaviour when interacting with other resources. Favour setting GH_TOKEN for fine-grained personal access token usage.

Alternatively, gh will use the authentication token found in environment variables. This method is most suitable for "headless" use of gh such as in automation. See gh help environment for more info.

To use gh in GitHub Actions, add GH_TOKEN: ${{ github.token }} to env.

The git protocol to use for git operations on this host can be set with --git-protocol, or during the interactive prompting. Although login is for a single account on a host, setting the git protocol will take effect for all users on the host.

Specifying ssh for the git protocol will detect existing SSH keys to upload, prompting to create and upload a new key if one is not found. This can be skipped with --skip-ssh-key flag.

For more information on OAuth scopes, see https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps/.

**Examples:**

Example 1 (unknown):
```unknown
gh auth login [flags]
```

Example 2 (bash):
```bash
# Start interactive setup
$ gh auth login

# Open a browser to authenticate and copy one-time OAuth code to clipboard
$ gh auth login --web --clipboard

# Authenticate against github.com by reading the token from a file
$ gh auth login --with-token < mytoken.txt

# Authenticate with specific host
$ gh auth login --hostname enterprise.internal
```

---

## gh attestation trusted-root

**URL:** https://cli.github.com/manual/gh_attestation_trusted-root

**Contents:**
- gh attestation trusted-root
  - Options
  - Examples
  - See also

Output contents for a trusted_root.jsonl file, likely for offline verification.

When using gh attestation verify, if your machine is on the internet, this will happen automatically. But to do offline verification, you need to supply a trusted root file with --custom-trusted-root; this command will help you fetch a trusted_root.jsonl file for that purpose.

You can call this command without any flags to get a trusted root file covering the Sigstore Public Good Instance as well as GitHub's Sigstore instance.

Otherwise you can use --tuf-url to specify the URL of a custom TUF repository mirror, and --tuf-root should be the path to the root.json file that you securely obtained out-of-band.

If you just want to verify the integrity of your local TUF repository, and don't want the contents of a trusted_root.jsonl file, use --verify-only.

**Examples:**

Example 1 (unknown):
```unknown
gh attestation trusted-root [--tuf-url <url> --tuf-root <file-path>] [--verify-only] [flags]
```

Example 2 (bash):
```bash
# Get a trusted_root.jsonl for both Sigstore Public Good and GitHub's instance
$ gh attestation trusted-root
```

---

## gh gist edit

**URL:** https://cli.github.com/manual/gh_gist_edit

**Contents:**
- gh gist edit
  - Options
  - See also

Edit one of your gists

**Examples:**

Example 1 (unknown):
```unknown
gh gist edit {<id> | <url>} [<filename>] [flags]
```

---

## gh config list

**URL:** https://cli.github.com/manual/gh_config_list

**Contents:**
- gh config list
  - Options
  - ALIASES
  - See also

Print a list of configuration keys and values

**Examples:**

Example 1 (unknown):
```unknown
gh config list [flags]
```

---

## gh variable set

**URL:** https://cli.github.com/manual/gh_variable_set

**Contents:**
- gh variable set
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Set a value for a variable on one of the following levels:

Organization variable can optionally be restricted to only be available to specific repositories.

**Examples:**

Example 1 (unknown):
```unknown
gh variable set <variable-name> [flags]
```

Example 2 (bash):
```bash
# Add variable value for the current repository in an interactive prompt
$ gh variable set MYVARIABLE

# Read variable value from an environment variable
$ gh variable set MYVARIABLE --body "$ENV_VALUE"

# Read variable value from a file
$ gh variable set MYVARIABLE < myfile.txt

# Set variable for a deployment environment in the current repository
$ gh variable set MYVARIABLE --env myenvironment

# Set organization-level variable visible to both public and private repositories
$ gh variable set MYVARIABLE --org myOrg --visibility all

# Set organization-level variable visible to specific repositories
$ gh variable set MYVARIABLE --org myOrg --repos repo1,repo2,repo3

# Set multiple variables imported from the ".env" file
$ gh variable set -f .env
```

---

## gh gist view

**URL:** https://cli.github.com/manual/gh_gist_view

**Contents:**
- gh gist view
  - Options
  - See also

View the given gist or select from recent gists.

**Examples:**

Example 1 (unknown):
```unknown
gh gist view [<id> | <url>] [flags]
```

---

## gh alias delete

**URL:** https://cli.github.com/manual/gh_alias_delete

**Contents:**
- gh alias delete
  - Options
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh alias delete {<alias> | --all} [flags]
```

---

## gh alias import

**URL:** https://cli.github.com/manual/gh_alias_import

**Contents:**
- gh alias import
  - Options
  - Examples
  - See also

Import aliases from the contents of a YAML file.

Aliases should be defined as a map in YAML, where the keys represent aliases and the values represent the corresponding expansions. An example file should look like the following:

Use - to read aliases (in YAML format) from standard input.

The output from gh alias list can be used to produce a YAML file containing your aliases, which you can use to import them from one machine to another. Run gh help alias list to learn more.

**Examples:**

Example 1 (unknown):
```unknown
gh alias import [<filename> | -] [flags]
```

Example 2 (unknown):
```unknown
bugs: issue list --label=bug
igrep: '!gh issue list --label="$1" | grep "$2"'
features: |-
    issue list
    --label=enhancement
```

Example 3 (bash):
```bash
# Import aliases from a file
$ gh alias import aliases.yml

# Import aliases from standard input
$ gh alias import -
```

---

## gh codespace cp

**URL:** https://cli.github.com/manual/gh_codespace_cp

**Contents:**
- gh codespace cp
  - Options
  - Examples
  - See also

The cp command copies files between the local and remote file systems.

As with the UNIX cp command, the first argument specifies the source and the last specifies the destination; additional sources may be specified after the first, if the destination is a directory.

The --recursive flag is required if any source is a directory.

A remote: prefix on any file name argument indicates that it refers to the file system of the remote (Codespace) machine. It is resolved relative to the home directory of the remote user.

By default, remote file names are interpreted literally. With the --expand flag, each such argument is treated in the manner of scp, as a Bash expression to be evaluated on the remote machine, subject to expansion of tildes, braces, globs, environment variables, and backticks. For security, do not use this flag with arguments provided by untrusted users; see https://lwn.net/Articles/835962/ for discussion.

By default, the cp command will create a public/private ssh key pair to authenticate with the codespace inside the ~/.ssh directory.

**Examples:**

Example 1 (unknown):
```unknown
gh codespace cp [-e] [-r] [-- [<scp flags>...]] <sources>... <dest>
```

Example 2 (bash):
```bash
$ gh codespace cp -e README.md 'remote:/workspaces/$RepositoryName/'
$ gh codespace cp -e 'remote:~/*.go' ./gofiles/
$ gh codespace cp -e 'remote:/workspaces/myproj/go.{mod,sum}' ./gofiles/
$ gh codespace cp -e -- -F ~/.ssh/codespaces_config 'remote:~/*.go' ./gofiles/
```

---

## gh attestation

**URL:** https://cli.github.com/manual/gh_attestation

**Contents:**
- gh attestation
  - Available commands
  - ALIASES
  - See also

Download and verify artifact attestations.

---

## gh codespace jupyter

**URL:** https://cli.github.com/manual/gh_codespace_jupyter

**Contents:**
- gh codespace jupyter
  - Options
  - See also

Open a codespace in JupyterLab

**Examples:**

Example 1 (unknown):
```unknown
gh codespace jupyter [flags]
```

---

## gh gist rename

**URL:** https://cli.github.com/manual/gh_gist_rename

**Contents:**
- gh gist rename
  - See also

Rename a file in the given gist ID / URL.

**Examples:**

Example 1 (unknown):
```unknown
gh gist rename {<id> | <url>} <old-filename> <new-filename>
```

---

## gh completion

**URL:** https://cli.github.com/manual/gh_completion

**Contents:**
- gh completion
  - bash
  - zsh
  - fish
  - PowerShell
  - Options
  - See also

Generate shell completion scripts for GitHub CLI commands.

When installing GitHub CLI through a package manager, it's possible that no additional shell configuration is necessary to gain completion support. For Homebrew, see https://docs.brew.sh/Shell-Completion

If you need to set up completions manually, follow the instructions below. The exact config file locations might vary based on your system. Make sure to restart your shell before testing whether completions are working.

First, ensure that you install bash-completion using your package manager.

After, add this to your ~/.bash_profile:

Generate a _gh completion script and put it somewhere in your $fpath:

Ensure that the following is present in your ~/.zshrc:

Zsh version 5.7 or later is recommended.

Generate a gh.fish completion script:

Open your profile script with:

Add the line and save the file:

**Examples:**

Example 1 (unknown):
```unknown
gh completion -s <shell>
```

Example 2 (unknown):
```unknown
eval "$(gh completion -s bash)"
```

Example 3 (unknown):
```unknown
gh completion -s zsh > /usr/local/share/zsh/site-functions/_gh
```

Example 4 (unknown):
```unknown
autoload -U compinit
compinit -i
```

---

## gh

**URL:** https://cli.github.com/manual/gh

**Contents:**
- gh
  - Core commands
  - GitHub Actions commands
  - Additional commands
  - Options
  - Examples

Work seamlessly with GitHub from the command line.

**Examples:**

Example 1 (bash):
```bash
$ gh issue create
$ gh repo clone cli/cli
$ gh pr checkout 321
```

---

## gh gpg-key add

**URL:** https://cli.github.com/manual/gh_gpg-key_add

**Contents:**
- gh gpg-key add
  - Options
  - See also

Add a GPG key to your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh gpg-key add [<key-file>] [flags]
```

---

## gh codespace ports visibility

**URL:** https://cli.github.com/manual/gh_codespace_ports_visibility

**Contents:**
- gh codespace ports visibility
  - Options inherited from parent commands
  - Examples
  - See also

Change the visibility of the forwarded port

**Examples:**

Example 1 (unknown):
```unknown
gh codespace ports visibility <port>:{public|private|org}...
```

Example 2 (bash):
```bash
$ gh codespace ports visibility 80:org 3000:private 8000:public
```

---

## gh status

**URL:** https://cli.github.com/manual/gh_status

**Contents:**
- gh status
  - Options
  - Examples
  - See also

The status command prints information about your work on GitHub across all the repositories you're subscribed to, including:

**Examples:**

Example 1 (unknown):
```unknown
gh status [flags]
```

Example 2 (bash):
```bash
$ gh status -e cli/cli -e cli/go-gh # Exclude multiple repositories
$ gh status -o cli # Limit results to a single organization
```

---

## gh gpg-key delete

**URL:** https://cli.github.com/manual/gh_gpg-key_delete

**Contents:**
- gh gpg-key delete
  - Options
  - See also

Delete a GPG key from your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh gpg-key delete <key-id> [flags]
```

---

## gh gpg-key

**URL:** https://cli.github.com/manual/gh_gpg-key

**Contents:**
- gh gpg-key
  - Available commands
  - See also

Manage GPG keys registered with your GitHub account.

---

## gh codespace rebuild

**URL:** https://cli.github.com/manual/gh_codespace_rebuild

**Contents:**
- gh codespace rebuild
  - Options
  - See also

Rebuilding recreates your codespace.

Your code and any current changes will be preserved. Your codespace will be rebuilt using your working directory's dev container. A full rebuild also removes cached Docker images.

**Examples:**

Example 1 (unknown):
```unknown
gh codespace rebuild [flags]
```

---

## gh secret delete

**URL:** https://cli.github.com/manual/gh_secret_delete

**Contents:**
- gh secret delete
  - Options
  - Options inherited from parent commands
  - ALIASES
  - See also

Delete a secret on one of the following levels:

**Examples:**

Example 1 (unknown):
```unknown
gh secret delete <secret-name> [flags]
```

---

## gh config set

**URL:** https://cli.github.com/manual/gh_config_set

**Contents:**
- gh config set
  - Options
  - Examples
  - See also

Update configuration with a value for the given key

**Examples:**

Example 1 (unknown):
```unknown
gh config set <key> <value> [flags]
```

Example 2 (bash):
```bash
$ gh config set editor vim
$ gh config set editor "code --wait"
$ gh config set git_protocol ssh --host github.com
$ gh config set prompt disabled
```

---

## gh gist list

**URL:** https://cli.github.com/manual/gh_gist_list

**Contents:**
- gh gist list
  - Options
  - ALIASES
  - Examples
  - See also

List gists from your user account.

You can use a regular expression to filter the description, file names, or even the content of files in the gist using --filter.

For supported regular expression syntax, see https://pkg.go.dev/regexp/syntax.

Use --include-content to include content of files, noting that this will be slower and increase the rate limit used. Instead of printing a table, code will be printed with highlights similar to gh search code:

No highlights or other color is printed when output is redirected.

**Examples:**

Example 1 (unknown):
```unknown
gh gist list [flags]
```

Example 2 (unknown):
```unknown
{{gist ID}} {{file name}}
    {{description}}
        {{matching lines from content}}
```

Example 3 (bash):
```bash
# List all secret gists from your user account
$ gh gist list --secret

# Find all gists from your user account mentioning "octo" anywhere
$ gh gist list --filter octo --include-content
```

---

## gh variable delete

**URL:** https://cli.github.com/manual/gh_variable_delete

**Contents:**
- gh variable delete
  - Options
  - Options inherited from parent commands
  - ALIASES
  - See also

Delete a variable on one of the following levels:

**Examples:**

Example 1 (unknown):
```unknown
gh variable delete <variable-name> [flags]
```

---

## gh codespace stop

**URL:** https://cli.github.com/manual/gh_codespace_stop

**Contents:**
- gh codespace stop
  - Options
  - See also

Stop a running codespace

**Examples:**

Example 1 (unknown):
```unknown
gh codespace stop [flags]
```

---

## gh auth

**URL:** https://cli.github.com/manual/gh_auth

**Contents:**
- gh auth
  - Available commands
  - See also

Authenticate gh and git with GitHub

---

## gh gist delete

**URL:** https://cli.github.com/manual/gh_gist_delete

**Contents:**
- gh gist delete
  - Options
  - Examples
  - See also

Delete a GitHub gist.

To delete a gist interactively, use gh gist delete with no arguments.

To delete a gist non-interactively, supply the gist id or url.

**Examples:**

Example 1 (unknown):
```unknown
gh gist delete {<id> | <url>} [flags]
```

Example 2 (bash):
```bash
# Delete a gist interactively
$ gh gist delete

# Delete a gist non-interactively
$ gh gist delete 1234
```

---

## gh ssh-key delete

**URL:** https://cli.github.com/manual/gh_ssh-key_delete

**Contents:**
- gh ssh-key delete
  - Options
  - See also

Delete an SSH key from your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh ssh-key delete <id> [flags]
```

---

## gh ssh-key list

**URL:** https://cli.github.com/manual/gh_ssh-key_list

**Contents:**
- gh ssh-key list
  - ALIASES
  - See also

Lists SSH keys in your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh ssh-key list
```

---

## gh codespace code

**URL:** https://cli.github.com/manual/gh_codespace_code

**Contents:**
- gh codespace code
  - Options
  - See also

Open a codespace in Visual Studio Code

**Examples:**

Example 1 (unknown):
```unknown
gh codespace code [flags]
```

---

## gh secret set

**URL:** https://cli.github.com/manual/gh_secret_set

**Contents:**
- gh secret set
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Set a value for a secret on one of the following levels:

Organization and user secrets can optionally be restricted to only be available to specific repositories.

Secret values are locally encrypted before being sent to GitHub.

**Examples:**

Example 1 (unknown):
```unknown
gh secret set <secret-name> [flags]
```

Example 2 (bash):
```bash
# Paste secret value for the current repository in an interactive prompt
$ gh secret set MYSECRET

# Read secret value from an environment variable
$ gh secret set MYSECRET --body "$ENV_VALUE"

# Set secret for a specific remote repository
$ gh secret set MYSECRET --repo origin/repo --body "$ENV_VALUE"

# Read secret value from a file
$ gh secret set MYSECRET < myfile.txt

# Set secret for a deployment environment in the current repository
$ gh secret set MYSECRET --env myenvironment

# Set organization-level secret visible to both public and private repositories
$ gh secret set MYSECRET --org myOrg --visibility all

# Set organization-level secret visible to specific repositories
$ gh secret set MYSECRET --org myOrg --repos repo1,repo2,repo3

# Set organization-level secret visible to no repositories
$ gh secret set MYSECRET --org myOrg --no-repos-selected

# Set user-level secret for Codespaces
$ gh secret set MYSECRET --user

# Set repository-level secret for Dependabot
$ gh secret set MYSECRET --app dependabot

# Set multiple secrets imported from the ".env" file
$ gh secret set -f .env

# Set multiple secrets from stdin
$ gh secret set -f - < myfile.txt
```

---

## gh org list

**URL:** https://cli.github.com/manual/gh_org_list

**Contents:**
- gh org list
  - Options
  - ALIASES
  - Examples
  - See also

List organizations for the authenticated user.

**Examples:**

Example 1 (unknown):
```unknown
gh org list [flags]
```

Example 2 (bash):
```bash
# List the first 30 organizations
$ gh org list

# List more organizations
$ gh org list --limit 100
```

---

## gh secret list

**URL:** https://cli.github.com/manual/gh_secret_list

**Contents:**
- gh secret list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List secrets on one of the following levels:

name, numSelectedRepos, selectedReposURL, updatedAt, visibility

**Examples:**

Example 1 (unknown):
```unknown
gh secret list [flags]
```

---

## gh auth refresh

**URL:** https://cli.github.com/manual/gh_auth_refresh

**Contents:**
- gh auth refresh
  - Options
  - Examples
  - See also

Expand or fix the permission scopes for stored credentials for active account.

The --scopes flag accepts a comma separated list of scopes you want your gh credentials to have. If no scopes are provided, the command maintains previously added scopes.

The --remove-scopes flag accepts a comma separated list of scopes you want to remove from your gh credentials. Scope removal is idempotent. The minimum set of scopes (repo, read:org, and gist) cannot be removed.

The --reset-scopes flag resets the scopes for your gh credentials to the default set of scopes for your auth flow.

If you have multiple accounts in gh auth status and want to refresh the credentials for an inactive account, you will have to use gh auth switch to that account first before using this command, and then switch back when you are done.

For more information on OAuth scopes, see https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps/.

**Examples:**

Example 1 (unknown):
```unknown
gh auth refresh [flags]
```

Example 2 (bash):
```bash
# Open a browser to add write:org and read:public_key scopes
$ gh auth refresh --scopes write:org,read:public_key

# Open a browser to ensure your authentication credentials have the correct minimum scopes
$ gh auth refresh

# Open a browser to idempotently remove the delete_repo scope
$ gh auth refresh --remove-scopes delete_repo

# Open a browser to re-authenticate with the default minimum scopes
$ gh auth refresh --reset-scopes

# Open a browser to re-authenticate and copy one-time OAuth code to clipboard
$ gh auth refresh --clipboard
```

---

## gh cache delete

**URL:** https://cli.github.com/manual/gh_cache_delete

**Contents:**
- gh cache delete
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Delete GitHub Actions caches.

Deletion requires authorization with the repo scope.

**Examples:**

Example 1 (unknown):
```unknown
gh cache delete [<cache-id> | <cache-key> | --all] [flags]
```

Example 2 (bash):
```bash
# Delete a cache by id
$ gh cache delete 1234

# Delete a cache by key
$ gh cache delete cache-key

# Delete a cache by id in a specific repo
$ gh cache delete 1234 --repo cli/cli

# Delete a cache by key and branch ref
$ gh cache delete cache-key --ref refs/heads/feature-branch

# Delete a cache by key and PR ref
$ gh cache delete cache-key --ref refs/pull/<PR-number>/merge

# Delete all caches (exit code 1 on no caches)
$ gh cache delete --all

# Delete all caches (exit code 0 on no caches)
$ gh cache delete --all --succeed-on-no-caches
```

---

## gh config clear-cache

**URL:** https://cli.github.com/manual/gh_config_clear-cache

**Contents:**
- gh config clear-cache
  - Examples
  - See also

**Examples:**

Example 1 (unknown):
```unknown
gh config clear-cache
```

Example 2 (bash):
```bash
# Clear the cli cache
$ gh config clear-cache
```

---

## gh codespace logs

**URL:** https://cli.github.com/manual/gh_codespace_logs

**Contents:**
- gh codespace logs
  - Options
  - See also

Access codespace logs

**Examples:**

Example 1 (unknown):
```unknown
gh codespace logs [flags]
```

---

## gh alias

**URL:** https://cli.github.com/manual/gh_alias

**Contents:**
- gh alias
  - Available commands
  - See also

Aliases can be used to make shortcuts for gh commands or to compose multiple commands.

Run gh help alias set to learn more.

---

## gh cache list

**URL:** https://cli.github.com/manual/gh_cache_list

**Contents:**
- gh cache list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - Examples
  - See also

List GitHub Actions caches

createdAt, id, key, lastAccessedAt, ref, sizeInBytes, version

**Examples:**

Example 1 (unknown):
```unknown
gh cache list [flags]
```

Example 2 (bash):
```bash
# List caches for current repository
$ gh cache list

# List caches for specific repository
$ gh cache list --repo cli/cli

# List caches sorted by least recently accessed
$ gh cache list --sort last_accessed_at --order asc

# List caches that have keys matching a prefix (or that match exactly)
$ gh cache list --key key-prefix

# List caches for a specific branch, replace <branch-name> with the actual branch name
$ gh cache list --ref refs/heads/<branch-name>

# List caches for a specific pull request, replace <pr-number> with the actual pull request number
$ gh cache list --ref refs/pull/<pr-number>/merge
```

---

## gh codespace ports

**URL:** https://cli.github.com/manual/gh_codespace_ports

**Contents:**
- gh codespace ports
  - Available commands
  - Options
  - JSON Fields
  - See also

List ports in a codespace

browseUrl, label, sourcePort, visibility

**Examples:**

Example 1 (unknown):
```unknown
gh codespace ports [flags]
```

---

## gh auth logout

**URL:** https://cli.github.com/manual/gh_auth_logout

**Contents:**
- gh auth logout
  - Options
  - Examples
  - See also

Remove authentication for a GitHub account.

This command removes the stored authentication configuration for an account. The authentication configuration is only removed locally.

This command does not revoke authentication tokens.

To revoke all authentication tokens generated by the GitHub CLI:

Note: this procedure will revoke all authentication tokens ever generated by the GitHub CLI across all your devices.

For more information about revoking OAuth application tokens, see: https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/reviewing-your-authorized-oauth-apps

**Examples:**

Example 1 (unknown):
```unknown
gh auth logout [flags]
```

Example 2 (bash):
```bash
# Select what host and account to log out of via a prompt
$ gh auth logout

# Log out of a specific host and specific account
$ gh auth logout --hostname enterprise.internal --user monalisa
```

---

## GitHub CLI manual

**URL:** https://cli.github.com/manual/

**Contents:**
- GitHub CLI manual
- Installation
- Configuration
- GitHub Enterprise
- Support

GitHub CLI, or gh, is a command-line interface to GitHub for use in your terminal or your scripts.

You can find installation instructions on our README.

Run gh auth login to authenticate with your GitHub account. Alternatively, gh will respect the GITHUB_TOKEN environment variable.

To set your preferred editor, use gh config set editor <editor>. Read more about gh config and environment variables.

Declare your aliases for often-used commands with gh alias set.

GitHub CLI supports GitHub Enterprise Server 2.20 and above. To authenticate with a GitHub instance, run:

To define this host as a default for all GitHub CLI commands, set the GH_HOST environment variable:

Finally, to authenticate commands in scripting mode or automation, set the GH_ENTERPRISE_TOKEN:

Ask usage questions and send us feedback in Discussions

Report bugs or search for existing feature requests in our issue tracker

**Examples:**

Example 1 (unknown):
```unknown
gh auth login --hostname <hostname>
```

Example 2 (unknown):
```unknown
export GH_HOST=<hostname>
```

Example 3 (unknown):
```unknown
export GH_ENTERPRISE_TOKEN=<access-token>
```

---

## gh auth token

**URL:** https://cli.github.com/manual/gh_auth_token

**Contents:**
- gh auth token
  - Options
  - See also

This command outputs the authentication token for an account on a given GitHub host.

Without the --hostname flag, the default host is chosen.

Without the --user flag, the active account for the host is chosen.

**Examples:**

Example 1 (unknown):
```unknown
gh auth token [flags]
```

---

## gh agent-task view

**URL:** https://cli.github.com/manual/gh_agent-task_view

**Contents:**
- gh agent-task view
  - Options
  - Examples
  - See also

View an agent task session.

**Examples:**

Example 1 (unknown):
```unknown
gh agent-task view [<session-id> | <pr-number> | <pr-url> | <pr-branch>] [flags]
```

Example 2 (bash):
```bash
# View an agent task by session ID
$ gh agent-task view e2fa49d2-f164-4a56-ab99-498090b8fcdf

# View an agent task by pull request number in current repo
$ gh agent-task view 12345

# View an agent task by pull request number
$ gh agent-task view --repo OWNER/REPO 12345

# View an agent task by pull request reference
$ gh agent-task view OWNER/REPO#12345

# View a pull request agents tasks in the browser
$ gh agent-task view 12345 --web
```

---

## gh ssh-key add

**URL:** https://cli.github.com/manual/gh_ssh-key_add

**Contents:**
- gh ssh-key add
  - Options
  - See also

Add an SSH key to your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh ssh-key add [<key-file>] [flags]
```

---

## gh codespace ssh

**URL:** https://cli.github.com/manual/gh_codespace_ssh

**Contents:**
- gh codespace ssh
  - Options
  - Examples
  - See also

The ssh command is used to SSH into a codespace. In its simplest form, you can run gh cs ssh, select a codespace interactively, and connect.

The ssh command will automatically create a public/private ssh key pair in the ~/.ssh directory if you do not have an existing valid key pair. When selecting the key pair to use, the preferred order is:

The ssh command also supports deeper integration with OpenSSH using a --config option that generates per-codespace ssh configuration in OpenSSH format. Including this configuration in your ~/.ssh/config improves the user experience of tools that integrate with OpenSSH, such as Bash/Zsh completion of ssh hostnames, remote path completion for scp/rsync/sshfs, git ssh remotes, and so on.

Once that is set up (see the second example below), you can ssh to codespaces as if they were ordinary remote hosts (using ssh, not gh cs ssh).

Note that the codespace you are connecting to must have an SSH server pre-installed. If the docker image being used for the codespace does not have an SSH server, install it in your Dockerfile or, for codespaces that use Debian-based images, you can add the following to your devcontainer.json:

**Examples:**

Example 1 (unknown):
```unknown
gh codespace ssh [<flags>...] [-- <ssh-flags>...] [<command>]
```

Example 2 (unknown):
```unknown
"features": {
	"ghcr.io/devcontainers/features/sshd:1": {
		"version": "latest"
	}
}
```

Example 3 (bash):
```bash
$ gh codespace ssh

$ gh codespace ssh --config > ~/.ssh/codespaces
$ printf 'Match all\nInclude ~/.ssh/codespaces\n' >> ~/.ssh/config
```

---

## gh auth switch

**URL:** https://cli.github.com/manual/gh_auth_switch

**Contents:**
- gh auth switch
  - Options
  - Examples
  - See also

Switch the active account for a GitHub host.

This command changes the authentication configuration that will be used when running commands targeting the specified GitHub host.

If the specified host has two accounts, the active account will be switched automatically. If there are more than two accounts, disambiguation will be required either through the --user flag or an interactive prompt.

For a list of authenticated accounts you can run gh auth status.

**Examples:**

Example 1 (unknown):
```unknown
gh auth switch [flags]
```

Example 2 (bash):
```bash
# Select what host and account to switch to via a prompt
$ gh auth switch

# Switch the active account on a specific host to a specific user
$ gh auth switch --hostname enterprise.internal --user monalisa
```

---

## gh config

**URL:** https://cli.github.com/manual/gh_config

**Contents:**
- gh config
  - Available commands
  - See also

Display or change configuration settings for gh.

Current respected settings:

---

## gh ssh-key

**URL:** https://cli.github.com/manual/gh_ssh-key

**Contents:**
- gh ssh-key
  - Available commands
  - See also

Manage SSH keys registered with your GitHub account.

---

## gh gpg-key list

**URL:** https://cli.github.com/manual/gh_gpg-key_list

**Contents:**
- gh gpg-key list
  - ALIASES
  - See also

Lists GPG keys in your GitHub account

**Examples:**

Example 1 (unknown):
```unknown
gh gpg-key list
```

---

## gh browse

**URL:** https://cli.github.com/manual/gh_browse

**Contents:**
- gh browse
  - Options
  - Examples
  - See also

Transition from the terminal to the web browser to view and interact with:

**Examples:**

Example 1 (unknown):
```unknown
gh browse [<number> | <path> | <commit-sha>] [flags]
```

Example 2 (bash):
```bash
# Open the home page of the current repository
$ gh browse

# Open the script directory of the current repository
$ gh browse script/

# Open issue or pull request 217
$ gh browse 217

# Open commit page
$ gh browse 77507cd94ccafcf568f8560cfecde965fcfa63

# Open repository settings
$ gh browse --settings

# Open main.go at line 312
$ gh browse main.go:312

# Open main.go with the repository at head of bug-fix branch
$ gh browse main.go --branch bug-fix

# Open main.go with the repository at commit 775007cd
$ gh browse main.go --commit=77507cd94ccafcf568f8560cfecde965fcfa63
```

---

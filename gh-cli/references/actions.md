# Gh-Cli - Actions

**Pages:** 15

---

## gh workflow run

**URL:** https://cli.github.com/manual/gh_workflow_run

**Contents:**
- gh workflow run
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Create a workflow_dispatch event for a given workflow.

This command will trigger GitHub Actions to run a given workflow file. The given workflow file must support an on.workflow_dispatch trigger in order to be run in this way.

If the workflow file supports inputs, they can be specified in a few ways:

**Examples:**

Example 1 (unknown):
```unknown
gh workflow run [<workflow-id> | <workflow-name>] [flags]
```

Example 2 (bash):
```bash
# Have gh prompt you for what workflow you'd like to run and interactively collect inputs
$ gh workflow run

# Run the workflow file 'triage.yml' at the remote's default branch
$ gh workflow run triage.yml

# Run the workflow file 'triage.yml' at a specified ref
$ gh workflow run triage.yml --ref my-branch

# Run the workflow file 'triage.yml' with command line inputs
$ gh workflow run triage.yml -f name=scully -f greeting=hello

# Run the workflow file 'triage.yml' with JSON via standard input
$ echo '{"name":"scully", "greeting":"hello"}' | gh workflow run triage.yml --json
```

---

## gh run view

**URL:** https://cli.github.com/manual/gh_run_view

**Contents:**
- gh run view
  - Options
  - Options inherited from parent commands
  - JSON Fields
  - Examples
  - See also

View a summary of a workflow run.

Due to platform limitations, gh may not always be able to associate jobs with their corresponding logs when using the primary method of fetching logs in zip format.

In such cases, gh will attempt to fetch logs for each job individually via the API. This fallback is slower and more resource-intensive. If more than 25 job logs are missing, the operation will fail with an error.

Additionally, due to similar platform constraints, some log lines may not be associated with a specific step within a job. In these cases, the step name will appear as UNKNOWN STEP in the log output.

attempt, conclusion, createdAt, databaseId, displayTitle, event, headBranch, headSha, jobs, name, number, startedAt, status, updatedAt, url, workflowDatabaseId, workflowName

**Examples:**

Example 1 (unknown):
```unknown
gh run view [<run-id>] [flags]
```

Example 2 (bash):
```bash
# Interactively select a run to view, optionally selecting a single job
$ gh run view

# View a specific run
$ gh run view 12345

# View a specific run with specific attempt number
$ gh run view 12345 --attempt 3

# View a specific job within a run
$ gh run view --job 456789

# View the full log for a specific job
$ gh run view --log --job 456789

# Exit non-zero if a run failed
$ gh run view 0451 --exit-status && echo "run pending or passed"
```

---

## gh workflow enable

**URL:** https://cli.github.com/manual/gh_workflow_enable

**Contents:**
- gh workflow enable
  - Options inherited from parent commands
  - See also

Enable a workflow, allowing it to be run and show up when listing workflows.

**Examples:**

Example 1 (unknown):
```unknown
gh workflow enable [<workflow-id> | <workflow-name>]
```

---

## gh workflow

**URL:** https://cli.github.com/manual/gh_workflow

**Contents:**
- gh workflow
  - Available commands
  - Options
  - See also

List, view, and run workflows in GitHub Actions.

---

## gh run

**URL:** https://cli.github.com/manual/gh_run

**Contents:**
- gh run
  - Available commands
  - Options
  - See also

List, view, and watch recent workflow runs from GitHub Actions.

---

## gh run rerun

**URL:** https://cli.github.com/manual/gh_run_rerun

**Contents:**
- gh run rerun
  - Options
  - Options inherited from parent commands
  - See also

Rerun an entire run, only failed jobs, or a specific job from a run.

Note that due to historical reasons, the --job flag may not take what you expect. Specifically, when navigating to a job in the browser, the URL looks like this: https://github.com/<owner>/<repo>/actions/runs/<run-id>/jobs/<number>.

However, this <number> should not be used with the --job flag and will result in the API returning 404 NOT FOUND. Instead, you can get the correct job IDs using the following command:

You will need to use databaseId field for triggering job re-runs.

**Examples:**

Example 1 (unknown):
```unknown
gh run rerun [<run-id>] [flags]
```

Example 2 (unknown):
```unknown
gh run view <run-id> --json jobs --jq '.jobs[] | {name, databaseId}'
```

---

## gh run watch

**URL:** https://cli.github.com/manual/gh_run_watch

**Contents:**
- gh run watch
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Watch a run until it completes, showing its progress.

By default, all steps are displayed. The --compact option can be used to only show the relevant/failed steps.

This command does not support authenticating via fine grained PATs as it is not currently possible to create a PAT with the checks:read permission.

**Examples:**

Example 1 (unknown):
```unknown
gh run watch <run-id> [flags]
```

Example 2 (bash):
```bash
# Watch a run until it's done
$ gh run watch

# Watch a run in compact mode
$ gh run watch --compact

# Run some other command when the run is finished
$ gh run watch && notify-send 'run is done!'
```

---

## gh workflow list

**URL:** https://cli.github.com/manual/gh_workflow_list

**Contents:**
- gh workflow list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List workflow files, hiding disabled workflows by default.

id, name, path, state

**Examples:**

Example 1 (unknown):
```unknown
gh workflow list [flags]
```

---

## gh run list

**URL:** https://cli.github.com/manual/gh_run_list

**Contents:**
- gh run list
  - Options
  - Options inherited from parent commands
  - ALIASES
  - JSON Fields
  - See also

List recent workflow runs.

Note that providing the workflow_name to the -w flag will not fetch disabled workflows. Also pass the -a flag to fetch disabled workflow runs using the workflow_name and the -w flag.

Runs created by organization and enterprise ruleset workflows will not display a workflow name due to GitHub API limitations.

attempt, conclusion, createdAt, databaseId, displayTitle, event, headBranch, headSha, name, number, startedAt, status, updatedAt, url, workflowDatabaseId, workflowName

**Examples:**

Example 1 (unknown):
```unknown
gh run list [flags]
```

---

## gh run download

**URL:** https://cli.github.com/manual/gh_run_download

**Contents:**
- gh run download
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

Download artifacts generated by a GitHub Actions workflow run.

The contents of each artifact will be extracted under separate directories based on the artifact name. If only a single artifact is specified, it will be extracted into the current directory.

By default, this command downloads the latest artifact created and uploaded through GitHub Actions. Because workflows can delete or overwrite artifacts, <run-id> must be used to select an artifact from a specific workflow run.

**Examples:**

Example 1 (unknown):
```unknown
gh run download [<run-id>] [flags]
```

Example 2 (bash):
```bash
# Download all artifacts generated by a workflow run
$ gh run download <run-id>

# Download a specific artifact within a run
$ gh run download <run-id> -n <name>

# Download specific artifacts across all runs in a repository
$ gh run download -n <name1> -n <name2>

# Select artifacts to download interactively
$ gh run download
```

---

## gh workflow disable

**URL:** https://cli.github.com/manual/gh_workflow_disable

**Contents:**
- gh workflow disable
  - Options inherited from parent commands
  - See also

Disable a workflow, preventing it from running or showing up when listing workflows.

**Examples:**

Example 1 (unknown):
```unknown
gh workflow disable [<workflow-id> | <workflow-name>]
```

---

## gh run cancel

**URL:** https://cli.github.com/manual/gh_run_cancel

**Contents:**
- gh run cancel
  - Options
  - Options inherited from parent commands
  - See also

Cancel a workflow run

**Examples:**

Example 1 (unknown):
```unknown
gh run cancel [<run-id>] [flags]
```

---

## gh run delete

**URL:** https://cli.github.com/manual/gh_run_delete

**Contents:**
- gh run delete
  - Options inherited from parent commands
  - Examples
  - See also

Delete a workflow run

**Examples:**

Example 1 (unknown):
```unknown
gh run delete [<run-id>]
```

Example 2 (bash):
```bash
# Interactively select a run to delete
$ gh run delete

# Delete a specific run
$ gh run delete 12345
```

---

## gh workflow view

**URL:** https://cli.github.com/manual/gh_workflow_view

**Contents:**
- gh workflow view
  - Options
  - Options inherited from parent commands
  - Examples
  - See also

View the summary of a workflow

**Examples:**

Example 1 (unknown):
```unknown
gh workflow view [<workflow-id> | <workflow-name> | <filename>] [flags]
```

Example 2 (bash):
```bash
# Interactively select a workflow to view
$ gh workflow view

# View a specific workflow
$ gh workflow view 0451
```

---

## gh attestation verify

**URL:** https://cli.github.com/manual/gh_attestation_verify

**Contents:**
- gh attestation verify
- Understanding Verification
- Loading Artifacts And Attestations
- Additional Policy Enforcement
  - Options
  - Examples
  - See also

Verify the integrity and provenance of an artifact using its associated cryptographically signed attestations.

An attestation is a claim (i.e. a provenance statement) made by an actor (i.e. a GitHub Actions workflow) regarding a subject (i.e. an artifact).

In order to verify an attestation, you must provide an artifact and validate:

By default, this command enforces the https://slsa.dev/provenance/v1 predicate type. To verify other attestation predicate types use the --predicate-type flag.

The "actor identity" consists of:

This identity is then validated against the attestation's certificate's SourceRepository, SourceRepositoryOwner, and SubjectAlternativeName (SAN) fields, among others.

It is up to you to decide how precisely you want to enforce this identity.

At a minimum, this command requires either:

The more precisely you specify the identity, the more control you will have over the security guarantees offered by the verification process.

Ideally, the path of the signer workflow is also validated using the --signer-workflow or --cert-identity flags.

Please note: if your attestation was generated via a reusable workflow then that reusable workflow is the signer whose identity needs to be validated. In this situation, you must use either the --signer-workflow or the --signer-repo flag.

For more options, see the other available flags.

To specify the artifact, this command requires:

By default, this command will attempt to fetch relevant attestations via the GitHub API using the values provided to --owner or --repo.

To instead fetch attestations from your artifact's OCI registry, use the --bundle-from-oci flag.

For offline verification using attestations stored on disk (c.f. the download command) provide a path to the --bundle flag.

Given the --format=json flag, upon successful verification this command will output a JSON array containing one entry per verified attestation.

This output can then be used for additional policy enforcement, i.e. by being piped into a policy engine.

Each object in the array contains two properties:

Within the verificationResult object you will find:

IMPORTANT: please note that only the signature.certificate and the verifiedTimestamps properties contain values that cannot be manipulated by the workflow that originated the attestation.

When dealing with attestations created within GitHub Actions, the contents of signature.certificate are populated directly from the OpenID Connect token that GitHub has generated. The contents of the verifiedTimestamps array are populated from the signed timestamps originating from either a transparency log or a timestamp authority – and likewise cannot be forged by users.

When designing policy enforcement using this output, special care must be taken when examining the contents of the statement.predicate property: should an attacker gain access to your workflow's execution context, they could then falsify the contents of the statement.predicate.

To mitigate this attack vector, consider using a "trusted builder": when generating an artifact, have the build and attestation signing occur within a reusable workflow whose execution cannot be influenced by input provided through the caller workflow.

See above re: --signer-workflow.

**Examples:**

Example 1 (unknown):
```unknown
gh attestation verify [<file-path> | oci://<image-uri>] [--owner | --repo] [flags]
```

Example 2 (bash):
```bash
# Verify an artifact linked with a repository
$ gh attestation verify example.bin --repo github/example

# Verify an artifact linked with an organization
$ gh attestation verify example.bin --owner github

# Verify an artifact and output the full verification result
$ gh attestation verify example.bin --owner github --format json

# Verify an OCI image using attestations stored on disk
$ gh attestation verify oci://<image-uri> --owner github --bundle sha256:foo.jsonl

# Verify an artifact signed with a reusable workflow
$ gh attestation verify example.bin --owner github --signer-repo actions/example
```

---

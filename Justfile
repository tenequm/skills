set shell := ["bash", "-euo", "pipefail", "-c"]

repo := "tenequm/skills"
homepage_base := "https://github.com/tenequm/skills/tree/main/skills/"
clawhub_base := "https://clawhub.ai/tenequm/skills"
just := just_executable()

# One-time per clone: git hooks plus the repo-local /update-skill command.
setup:
    lefthook install
    mkdir -p .claude/skills .agents/skills
    ln -sfn ../../skills/update-skill .claude/skills/update-skill
    ln -sfn ../../skills/update-skill .agents/skills/update-skill

# Local gate: skill policy, whitespace, secrets; regenerates README.md for you to stage.
check: lint readme hygiene

# Hook and CI gate: same checks, but fails if the staged README.md is stale.
check-ci: lint readme-check hygiene

# Dry-run every skill publish against ClawHub (network + `clawhub login`).
preflight:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v clawhub >/dev/null || { echo "clawhub CLI not found: npm install -g clawhub" >&2; exit 1; }
    one() {
      local d=$1 f=skills/$1/SKILL.md out err n
      get() { yq --front-matter=extract "$1 // \"\"" "$f" | tr -d ' '; }
      local v; v=$(get .metadata.version)
      local args=(--no-input skill publish "skills/$d" --slug "$d" --name "$d" --version "$v" --dry-run --json)
      local c; c=$(get .metadata.categories); [[ -z $c ]] || args+=(--categories "$c")
      local t; t=$(get .metadata.topics); [[ -z $t ]] || args+=(--topics "$t")
      n=$(git ls-files -- "skills/$d" | grep -vc '/\.' || true)
      err=$(mktemp)
      if ! out=$(clawhub "${args[@]}" 2>"$err"); then
        echo "$d: clawhub dry-run failed (logged in?): $(cat "$err") $out"; rm -f "$err"; return
      fi
      rm -f "$err"
      jq -r --arg d "$d" --arg v "$v" --argjson n "$n" '
        if .ok != true then "\($d): dry-run not ok: \(tojson)"
        elif .slug != $d then "\($d): resolved slug `\(.slug)`"
        elif .version != $v then "\($d): would publish \(.version), frontmatter says \($v)"
        elif .fileCount != $n then "\($d): would upload \(.fileCount) files, \($n) tracked - the CLI drops files it treats as registry-generated"
        else empty end' <<<"$out" 2>/dev/null || echo "$d: dry-run returned non-JSON: $out"
    }
    export -f one
    problems=$(ls skills | xargs -P 16 -I{} bash -c 'one "$1"' _ {})
    [[ -z $problems ]] || { echo "$problems" >&2; exit 1; }
    echo "Resolved $(ls skills | wc -l | tr -d ' ') publishes."

# Show what `release` would publish since the last `skills-*` tag (or `base`).
release-plan base="":
    @{{just}} _release plan "{{base}}"

# Publish changed skills to ClawHub and cut a GitHub release (CI on main).
release base="":
    @{{just}} _release run "{{base}}"

[private]
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    report=$({{just}} _skills-json | jq -r --arg home "{{homepage_base}}" '
      def csv: split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0));
      def slug: test("^[a-z0-9]+(-[a-z0-9]+)*$");
      def dupes: length != (unique | length);
      def nested: IN("openclaw", "clawdbot", "clawdis");
      ["integrations", "automation", "research", "development", "productivity", "communication",
       "creative", "knowledge", "agents", "operations", "security", "finance", "lifestyle", "other"] as $categories
      | ["approved", "audited", "certified", "clawhub", "community", "curated", "endorsed", "featured",
         "official", "officials", "openclaw", "recommended", "staff-pick", "trusted", "trusted-publisher",
         "verified"] as $reserved
      | ["allowed-tools", "compatibility", "description", "license", "metadata", "name",
         "command-arg-mode", "command-dispatch", "command-tool", "disable-model-invocation", "homepage",
         "user-invocable", "agent", "argument-hint", "arguments", "context", "effort", "hooks", "model",
         "when_to_use"] as $fields
      | ["always", "config", "emoji", "envVars", "homepage", "install", "nix", "os", "primaryEnv",
         "requires", "skillKey"] as $openclaw_fields
      | .[] | .dir as $d | .fm as $fm | .chars as $chars | .body as $body
      | ( if ($fm | type) != "object" then "E missing YAML frontmatter"
          else
            ($fm.name | if type != "string" then "E `name` must be a string"
              elif length > 64 then "E `name` exceeds 64 characters"
              elif (slug | not) then "E `name` must be lowercase and hyphen-separated"
              elif . != $d then "E `name` must match the directory name `\($d)`"
              else empty end),
            ($fm.description | if type != "string" then "E `description` must be a string"
              else gsub("^\\s+|\\s+$"; "") | length
                | if . == 0 then "E `description` must not be empty"
                  elif . > 250 then "E `description` is \(.) characters, over the 250-character limit"
                  else empty end end),
            (if $fm | has("compatibility") then $fm.compatibility
              | if type != "string" or length == 0 or length > 500
                then "E `compatibility` must be a string of 1-500 characters" else empty end
              else empty end),
            ($fm.metadata | if type != "object" then "E `metadata` mapping with `metadata.version` is required"
              else
                (to_entries[] | if (.key | nested) then (select(.value | type != "object") | "E `metadata.\(.key)` must be a mapping")
                  else (select(.value | type != "string") | "E `metadata.\(.key)` must be a string") end),
                (if (.version | type) != "string" or .version == "" then "E `metadata.version` must be a non-empty string" else empty end),
                (.openclaw | if . == null then "E `metadata.openclaw` is required"
                  elif type != "object" then empty
                  else
                    ((keys - $openclaw_fields) | select(length > 0) | "E `metadata.openclaw` has fields outside the ClawHub spec: \(join(", "))"),
                    (select(.homepage != "\($home)\($d)") | "E `metadata.openclaw.homepage` must be `\($home)\($d)`"),
                    (select((.emoji | type) != "string" or .emoji == "") | "E `metadata.openclaw.emoji` must be a non-empty string")
                  end),
                (.categories | if . == null then "E `metadata.categories` is required"
                  elif type != "string" then empty
                  else csv
                    | (select(length == 0) | "E `metadata.categories` must not be empty"),
                      ((. - $categories) | select(length > 0) | "E `metadata.categories` has slugs outside the ClawHub taxonomy: \(join(", "))"),
                      (select(dupes) | "E `metadata.categories` repeats a slug"),
                      (select(length > 3) | "E `metadata.categories` allows at most 3 slugs"),
                      (select(index("other") != null and length > 1) | "E `metadata.categories` must drop `other` next to a specific category")
                  end),
                (.topics | if type != "string" then empty
                  else csv
                    | (select(length == 0) | "E `metadata.topics` must not be empty when present"),
                      (select(length > 5) | "E `metadata.topics` allows at most 5 topics"),
                      (select(dupes) | "E `metadata.topics` repeats a topic"),
                      (.[] | (select(length > 48) | "E topic `\(.)` exceeds 48 characters"),
                             (select(slug | not) | "E topic `\(.)` must be lowercase and hyphen-separated"),
                             (select(IN($reserved[])) | "E topic `\(.)` is reserved by ClawHub"))
                  end)
              end),
            ((($fm | keys) - $fields) | select(length > 0) | "E unexpected top-level frontmatter fields: \(join(", "))")
          end ),
        (if $body == 0 then "E skill body must not be empty" else empty end),
        (if $chars > 50000 then "E SKILL.md is \($chars) bytes, over the 50000 hard ceiling: condense, or move conditionally-loaded content to references/"
         elif $chars > 25000 then "W SKILL.md is \($chars) bytes, over the recommended 25000: condense carefully"
         else empty end)
      | "\(.[0:1]) skills/\($d)/SKILL.md: \(.[2:])"')
    # Claude Code runs `!` + backtick at skill load even inside code fences and spans, so
    # doc examples of it must live in references/. Bare top-level directives are intentional.
    report+=$'\n'$(awk '
      function spans(line,   i, j, n, k, nr) {
        split("", rs); split("", rl); ns = 0; nr = 0; n = length(line); i = 1
        while (i <= n) {
          if (substr(line, i, 1) != "`") { i++; continue }
          for (j = i; j <= n && substr(line, j, 1) == "`"; j++);
          nr++; rs[nr] = i; rl[nr] = j - i; i = j
        }
        for (k = 1; k <= nr; k++) {
          for (j = k + 1; j <= nr && rl[j] != rl[k]; j++);
          if (j > nr) continue
          ns++; ss[ns] = rs[k] + rl[k]; se[ns] = rs[j]; k = j
        }
      }
      function report(msg) { printf "E %s: line %d: %s\n", FILENAME, FNR, msg }
      FNR == 1 { fm = 0; infence = 0; if (/^---[[:space:]]*$/) { fm = 1; next } }
      fm { if (/^---[[:space:]]*$/) fm = 0; next }
      {
        if (match($0, /^[[:space:]]*(```+|~~~+)/)) {
          run = substr($0, RSTART, RLENGTH); sub(/^[[:space:]]*/, "", run)
          info = substr($0, RSTART + RLENGTH); gsub(/^[[:space:]]+|[[:space:]]+$/, "", info)
          ch = substr(run, 1, 1)
          if (!infence) { infence = 1; fch = ch; flen = length(run); fexec = (substr(info, 1, 1) == "!"); next }
          if (ch == fch && length(run) >= flen && info == "") { infence = 0; next }
          if (ch == "`" && substr(info, 1, 1) == "!") { report("executable ```! block nested in a code fence still runs at skill load; move it to references/"); next }
        }
        if (infence && fexec) next
        spans($0)
        for (p = 1; p < length($0); p++) {
          if (substr($0, p, 2) != "!`" || (p > 1 && substr($0, p - 1, 1) !~ /[ \t]/)) continue
          hit = infence
          for (s = 1; s <= ns && !hit; s++) if (ss[s] <= p && p < se[s]) hit = 1
          if (hit) report("dynamic-injection doc example runs at skill load (the loader ignores code fences and spans); move it to references/ or break the !-backtick adjacency")
        }
      }' skills/*/SKILL.md)
    grep '^W ' <<<"$report" | cut -c3- >&2 || true
    if grep -q '^E ' <<<"$report"; then grep '^E ' <<<"$report" | cut -c3- >&2; exit 1; fi

[private]
readme:
    @{{just}} _readme-render > README.md.tmp && mv README.md.tmp README.md

# Compares against the index, so a regenerated but unstaged README.md still fails the hook.
[private]
readme-check:
    #!/usr/bin/env bash
    set -euo pipefail
    staged=$(mktemp); trap 'rm -f "$staged"' EXIT
    git show :README.md > "$staged"
    diff -q "$staged" <({{just}} _readme-render "$staged") >/dev/null || { echo "README.md is out of date: run just check and stage it" >&2; exit 1; }

[private]
hygiene:
    git -c core.whitespace=-space-before-tab diff --check "$(git hash-object -t tree /dev/null)"
    betterleaks dir -c .github/betterleaks.toml --no-banner --redact $(git ls-files | cut -d/ -f1 | sort -u)

[private]
_skills-json:
    #!/usr/bin/env bash
    set -euo pipefail
    for f in skills/*/SKILL.md; do
      d=${f#skills/}; d=${d%/SKILL.md}
      fm=$(yq --front-matter=extract -o=json -I0 . "$f" 2>/dev/null || echo null)
      body=$(awk 'FNR == 1 && /^---[[:space:]]*$/ { fm = 1; next } fm { if (/^---[[:space:]]*$/) fm = 0; next } { print }' "$f" | tr -d '[:space:]' | wc -c | tr -d ' ')
      jq -cn --arg dir "$d" --argjson fm "$fm" --argjson chars "$(wc -c < "$f" | tr -d ' ')" --argjson body "$body" '{$dir, $fm, $chars, $body}'
    done | jq -s .

[private]
_readme-render src="README.md":
    #!/usr/bin/env bash
    set -euo pipefail
    TABLE=$({{just}} _skills-json | jq -r --arg base "{{clawhub_base}}" '
      "| Skill | Version | ClawHub | Description |", "|-------|---------|---------|-------------|",
      (.[] | "| `\(.dir)` | \(.fm.metadata.version // "-") | [page](\($base)/\(.dir)) | \(.fm.description // "-" | gsub("\\s+"; " ") | gsub("^ | $"; "") | gsub("\\|"; "\\|")) |")') \
      awk '/<!-- GENERATED_SKILLS_TABLE_START -->/ { print; print ENVIRON["TABLE"]; skip = 1; next }
           /<!-- GENERATED_SKILLS_TABLE_END -->/ { skip = 0 } !skip' "{{src}}"

[private]
_release mode base:
    #!/usr/bin/env bash
    set -euo pipefail
    base="{{base}}"
    [[ -n $base ]] || base=$(git describe --tags --match 'skills-*' --abbrev=0 HEAD)
    head=$(git rev-parse HEAD)
    version_at() { git show "$1:skills/$2/SKILL.md" 2>/dev/null | yq --front-matter=extract '.metadata.version // ""' - 2>/dev/null || true; }
    field() { yq --front-matter=extract "$1 // \"\"" "skills/$2/SKILL.md" | tr -d ' '; }
    notes=$(mktemp); publish=""; bad=0
    for d in $(git diff --name-only "$base" "$head" -- skills/ | cut -d/ -f2 | sort -u); do
      if [[ ! -f skills/$d/SKILL.md ]]; then echo "- \`$d\` removed" >> "$notes"; continue; fi
      new=$(version_at "$head" "$d"); old=$(version_at "$base" "$d")
      if [[ $old == "$new" ]]; then echo "skills/$d changed but metadata.version is still $new" >&2; bad=1; continue; fi
      publish+=" $d"
      echo "- \`$d\` ${old:+$old -> }$new" >> "$notes"
      git log --format='  - %s' "$base..$head" -- "skills/$d" >> "$notes"
    done
    (( bad == 0 )) || exit 1
    [[ -s $notes ]] || { echo "No skill changes since $base."; exit 0; }
    echo "Release ${head:0:7} (since $base):"; cat "$notes"
    [[ "{{mode}}" == run ]] || exit 0
    failed=0
    for d in $publish; do
      args=(--no-input skill publish "skills/$d" --slug "$d" --name "$d" --version "$(field .metadata.version "$d")"
            --changelog "$(git log --format='- %s' "$base..$head" -- "skills/$d")" --tags latest
            --source-repo "{{repo}}" --source-commit "$head" --source-ref refs/heads/main --source-path "skills/$d")
      c=$(field .metadata.categories "$d"); [[ -z $c ]] || args+=(--categories "$c")
      t=$(field .metadata.topics "$d"); [[ -z $t ]] || args+=(--topics "$t")
      echo "Publishing $d"
      if ! out=$(clawhub "${args[@]}" 2>&1); then
        if [[ $out == *"already exists"* ]]; then echo "  already published"; else echo "  $out" >&2; failed=1; fi
      fi
    done
    # No tag on failure, so the next run retries this range; published versions skip.
    (( failed == 0 )) || exit 1
    gh release create "skills-${head:0:7}" --target "$head" --title "Skills release ${head:0:7}" --notes-file "$notes"

# Installation Workflow for Claude Skills

Complete guide to previewing, downloading, and installing Claude skills from GitHub.

## Installation Process Overview

1. **Preview** - Show skill details and requirements
2. **Confirm** - Get user approval
3. **Download** - Fetch skill files from GitHub
4. **Install** - Place in correct directory structure
5. **Verify** - Confirm installation success
6. **Setup** - Run any required setup steps

## Step 1: Preview Skill

### Fetch SKILL.md Content

```bash
# Get direct link to SKILL.md
skill_url="https://github.com/OWNER/REPO/blob/main/PATH/SKILL.md"
skill_path="PATH/SKILL.md"

# Fetch content (first 50 lines for preview)
gh api repos/OWNER/REPO/contents/$skill_path | \
  jq -r '.content' | base64 -d | head -50
```

### Extract Key Information

```bash
# Parse SKILL.md for important details
skill_content=$(gh api repos/OWNER/REPO/contents/$skill_path | jq -r '.content' | base64 -d)

# Extract name (first # heading)
skill_name=$(echo "$skill_content" | grep -m1 '^# ' | sed 's/^# //')

# Extract description (first paragraph after title)
description=$(echo "$skill_content" | sed -n '/^# /,/^$/p' | grep -v '^#' | head -1)

# Extract dependencies
dependencies=$(echo "$skill_content" | grep -A10 -i "dependencies\|requirements\|prerequisites" | head -10)

# Extract usage examples
examples=$(echo "$skill_content" | grep -A10 -i "usage\|example\|quick start" | head -15)
```

### Display Preview

```bash
cat <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Skill Preview: $skill_name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Description:
$description

⭐ Repository: $repo_full_name
🌟 Stars: $stars
🔄 Last Updated: $days_ago days ago

📋 Dependencies:
$dependencies

💡 Usage Example:
$examples

📎 Full Documentation:
$skill_url

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
```

## Step 2: Confirm Installation

### Check Existing Installation

```bash
# Determine skill directory name
skill_dir_name=$(echo "$skill_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
skill_dir=".claude/skills/$skill_dir_name"

# Check if already installed
if [ -d "$skill_dir" ]; then
  echo "⚠️  Skill '$skill_name' is already installed at: $skill_dir"
  echo ""
  echo "Options:"
  echo "  [U] Update (overwrite existing)"
  echo "  [K] Keep existing (cancel)"
  echo "  [B] Backup and install new"
  echo ""
  read -p "Choose option [U/K/B]: " choice

  case $choice in
    [Uu])
      echo "Overwriting existing installation..."
      ;;
    [Kk])
      echo "Keeping existing installation. Cancelled."
      exit 0
      ;;
    [Bb])
      backup_dir="${skill_dir}.backup.$(date +%s)"
      mv "$skill_dir" "$backup_dir"
      echo "✅ Backed up to: $backup_dir"
      ;;
    *)
      echo "Invalid option. Cancelled."
      exit 1
      ;;
  esac
fi
```

### Get User Confirmation

```bash
echo ""
echo "Install '$skill_name' to $skill_dir?"
echo ""
read -p "Continue? [y/N]: " confirm

if [[ ! "$confirm" =~ ^[Yy] ]]; then
  echo "Installation cancelled."
  exit 0
fi
```

## Step 3: Download Skill Files

### Determine Skill Structure

Skills can have different structures:

1. **Simple** - Single SKILL.md file
2. **Standard** - SKILL.md + reference files
3. **Plugin** - Nested in `skills/` subdirectory
4. **Complex** - Multiple files, scripts, dependencies

```bash
# Detect structure type
structure_type=$(detect_skill_structure "$repo" "$skill_path")

case $structure_type in
  "simple")
    download_simple_skill "$repo" "$skill_path" "$skill_dir"
    ;;
  "standard")
    download_standard_skill "$repo" "$skill_path" "$skill_dir"
    ;;
  "plugin")
    download_plugin_skill "$repo" "$skill_path" "$skill_dir"
    ;;
  "complex")
    download_complex_skill "$repo" "$skill_path" "$skill_dir"
    ;;
esac
```

### Download Simple Skill (SKILL.md only)

```bash
download_simple_skill() {
  local repo=$1
  local skill_path=$2
  local dest_dir=$3

  echo "📥 Downloading simple skill..."

  # Create destination directory
  mkdir -p "$dest_dir"

  # Download SKILL.md
  gh api "repos/$repo/contents/$skill_path" | \
    jq -r '.content' | base64 -d > "$dest_dir/SKILL.md"

  if [ -f "$dest_dir/SKILL.md" ]; then
    echo "✅ Downloaded SKILL.md"
  else
    echo "❌ Failed to download SKILL.md"
    return 1
  fi
}
```

### Download Standard Skill (with references)

```bash
download_standard_skill() {
  local repo=$1
  local skill_path=$2
  local dest_dir=$3

  echo "📥 Downloading standard skill..."

  # Get skill directory path from SKILL.md path
  skill_dir_path=$(dirname "$skill_path")

  # Get all files in skill directory
  gh api "repos/$repo/contents/$skill_dir_path?recursive=1" | \
    jq -r '.tree[] | select(.type == "blob") | .path' | \
    while read file_path; do
      # Calculate relative path
      rel_path=${file_path#$skill_dir_path/}
      dest_file="$dest_dir/$rel_path"

      # Create subdirectories
      mkdir -p "$(dirname "$dest_file")"

      # Download file
      gh api "repos/$repo/contents/$file_path" | \
        jq -r '.content' | base64 -d > "$dest_file"

      echo "  ✓ $rel_path"
    done

  echo "✅ Downloaded all skill files"
}
```

### Download Plugin Skill (nested structure)

```bash
download_plugin_skill() {
  local repo=$1
  local skill_path=$2
  local dest_dir=$3

  echo "📥 Downloading plugin skill..."
  echo "   (This may take a moment...)"

  # Clone repository to temporary location
  temp_dir=$(mktemp -d)
  gh repo clone "$repo" "$temp_dir" -- --depth 1 --quiet

  # Extract skill directory from SKILL.md path
  # Example: skills/playwright-skill/SKILL.md -> skills/playwright-skill
  skill_subdir=$(dirname "$skill_path")

  # Copy skill directory to destination
  if [ -d "$temp_dir/$skill_subdir" ]; then
    cp -r "$temp_dir/$skill_subdir/"* "$dest_dir/"
    echo "✅ Copied skill from $skill_subdir"
  else
    echo "❌ Skill directory not found: $skill_subdir"
    rm -rf "$temp_dir"
    return 1
  fi

  # Cleanup
  rm -rf "$temp_dir"
}
```

### Download Complex Skill (with setup)

```bash
download_complex_skill() {
  local repo=$1
  local skill_path=$2
  local dest_dir=$3

  echo "📥 Downloading complex skill..."

  # Use plugin download method
  download_plugin_skill "$repo" "$skill_path" "$dest_dir"

  # Check for dependencies
  if [ -f "$dest_dir/package.json" ]; then
    echo ""
    echo "📦 This skill has npm dependencies."
    echo "   Run: cd $dest_dir && npm install"
  fi

  if [ -f "$dest_dir/requirements.txt" ]; then
    echo ""
    echo "🐍 This skill has Python dependencies."
    echo "   Run: cd $dest_dir && pip install -r requirements.txt"
  fi

  if [ -f "$dest_dir/setup.sh" ]; then
    echo ""
    echo "🔧 This skill has a setup script."
    read -p "   Run setup.sh now? [y/N]: " run_setup
    if [[ "$run_setup" =~ ^[Yy] ]]; then
      (cd "$dest_dir" && bash setup.sh)
    fi
  fi
}
```

## Step 4: Verify Installation

### Check Required Files

```bash
verify_installation() {
  local skill_dir=$1
  local errors=0

  echo ""
  echo "🔍 Verifying installation..."

  # Check SKILL.md exists
  if [ ! -f "$skill_dir/SKILL.md" ]; then
    echo "  ❌ Missing SKILL.md"
    ((errors++))
  else
    echo "  ✅ SKILL.md present"
  fi

  # Check file permissions
  if [ ! -r "$skill_dir/SKILL.md" ]; then
    echo "  ❌ SKILL.md not readable"
    ((errors++))
  else
    echo "  ✅ File permissions OK"
  fi

  # Check for reference files (optional but good)
  if [ -d "$skill_dir/references" ]; then
    ref_count=$(find "$skill_dir/references" -type f | wc -l)
    echo "  ✅ Found $ref_count reference files"
  fi

  # Check for examples (optional)
  if [ -d "$skill_dir/examples" ]; then
    example_count=$(find "$skill_dir/examples" -type f | wc -l)
    echo "  ✅ Found $example_count example files"
  fi

  return $errors
}
```

### Validate SKILL.md Content

```bash
validate_skill_content() {
  local skill_file=$1

  # Check for required sections
  local has_title=$(grep -q '^# ' "$skill_file" && echo "yes" || echo "no")
  local has_description=$(grep -qi 'description\|what.*does' "$skill_file" && echo "yes" || echo "no")
  local has_usage=$(grep -qi 'usage\|example\|how.*use' "$skill_file" && echo "yes" || echo "no")

  if [ "$has_title" = "yes" ] && [ "$has_description" = "yes" ]; then
    echo "  ✅ SKILL.md structure valid"
    return 0
  else
    echo "  ⚠️  SKILL.md may be incomplete (missing title or description)"
    return 1
  fi
}
```

## Step 5: Post-Installation

### Run Setup Scripts

```bash
# Check for and run setup
if [ -f "$skill_dir/setup.sh" ]; then
  echo ""
  echo "🔧 Running setup script..."
  (cd "$skill_dir" && bash setup.sh)

  if [ $? -eq 0 ]; then
    echo "✅ Setup completed successfully"
  else
    echo "⚠️  Setup script had warnings (check above)"
  fi
fi
```

### Install Dependencies

```bash
# npm dependencies
if [ -f "$skill_dir/package.json" ]; then
  echo ""
  echo "📦 Installing npm dependencies..."
  (cd "$skill_dir" && npm install --silent)
  echo "✅ npm dependencies installed"
fi

# Python dependencies
if [ -f "$skill_dir/requirements.txt" ]; then
  echo ""
  echo "🐍 Installing Python dependencies..."
  pip install -q -r "$skill_dir/requirements.txt"
  echo "✅ Python dependencies installed"
fi
```

### Create Usage Instructions

```bash
cat <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Installation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Installed to: $skill_dir

🚀 Usage:
   Invoke the skill by typing: /$skill_dir_name
   Or let Claude auto-invoke when relevant

📖 Documentation:
   Read: $skill_dir/SKILL.md
   Examples: $skill_dir/examples/ (if available)

🔄 Update:
   Re-run installation to update to latest version

❌ Uninstall:
   rm -rf $skill_dir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
```

## Complete Installation Script

```bash
#!/bin/bash

install_skill() {
  local repo=$1
  local skill_path=$2
  local skill_name=$3

  # 1. Determine destination
  skill_dir_name=$(echo "$skill_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
  skill_dir=".claude/skills/$skill_dir_name"

  # 2. Preview
  echo "Fetching skill preview..."
  skill_content=$(gh api "repos/$repo/contents/$skill_path" | jq -r '.content' | base64 -d)
  description=$(echo "$skill_content" | sed -n '/^# /,/^$/p' | grep -v '^#' | head -1)

  echo ""
  echo "📦 $skill_name"
  echo "📝 $description"
  echo "📁 Will install to: $skill_dir"
  echo ""

  # 3. Confirm
  read -p "Install this skill? [y/N]: " confirm
  [[ ! "$confirm" =~ ^[Yy] ]] && { echo "Cancelled."; return 1; }

  # 4. Check existing
  if [ -d "$skill_dir" ]; then
    read -p "Skill exists. Overwrite? [y/N]: " overwrite
    [[ ! "$overwrite" =~ ^[Yy] ]] && { echo "Cancelled."; return 1; }
    rm -rf "$skill_dir"
  fi

  # 5. Download
  mkdir -p "$skill_dir"

  # Detect if plugin format or simple
  if [[ "$skill_path" == *"/skills/"* ]]; then
    # Plugin format - clone and extract
    temp_dir=$(mktemp -d)
    gh repo clone "$repo" "$temp_dir" -- --depth 1 --quiet
    skill_subdir=$(dirname "$skill_path")
    cp -r "$temp_dir/$skill_subdir/"* "$skill_dir/"
    rm -rf "$temp_dir"
  else
    # Simple format - direct download
    gh api "repos/$repo/contents/$skill_path" | \
      jq -r '.content' | base64 -d > "$skill_dir/SKILL.md"
  fi

  # 6. Verify
  if [ -f "$skill_dir/SKILL.md" ]; then
    echo "✅ Installation successful!"
    echo "📁 Location: $skill_dir"
    echo "🚀 Use: /$skill_dir_name"
  else
    echo "❌ Installation failed"
    return 1
  fi
}

# Usage:
# install_skill "lackeyjb/playwright-skill" "skills/playwright-skill/SKILL.md" "playwright-skill"
```

## Error Handling

### Common Issues

**Issue: Repository not found**
```bash
if ! gh api "repos/$repo" &>/dev/null; then
  echo "❌ Repository not found or not accessible: $repo"
  echo "   Check if the repository exists and is public"
  exit 1
fi
```

**Issue: SKILL.md not found**
```bash
if ! gh api "repos/$repo/contents/$skill_path" &>/dev/null; then
  echo "❌ SKILL.md not found at: $skill_path"
  echo "   Searching for SKILL.md in repository..."

  # Try to find it
  found_paths=$(gh api "repos/$repo/git/trees/main?recursive=1" | \
    jq -r '.tree[] | select(.path | contains("SKILL.md")) | .path')

  if [ -n "$found_paths" ]; then
    echo "   Found SKILL.md at:"
    echo "$found_paths" | sed 's/^/     /'
  else
    echo "   No SKILL.md found in repository"
  fi
  exit 1
fi
```

**Issue: Permission denied**
```bash
if [ ! -w ".claude/skills" ]; then
  echo "❌ Cannot write to .claude/skills directory"
  echo "   Check permissions: ls -la .claude/skills"
  exit 1
fi
```

**Issue: Network/API error**
```bash
if ! ping -c 1 api.github.com &>/dev/null; then
  echo "❌ Cannot reach GitHub API"
  echo "   Check your internet connection"
  exit 1
fi
```

---

**Summary:** The installation workflow ensures safe, verified installation of Claude skills with proper error handling, user confirmation, and post-installation setup.

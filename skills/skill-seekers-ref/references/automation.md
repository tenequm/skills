# Automation and CI/CD

## GitHub Actions - Weekly Skill Update

```yaml
name: Update AI Skills
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch: {}    # Manual trigger

jobs:
  update-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install skill-seekers
        run: pip install skill-seekers

      - name: Create React skill
        run: |
          skill-seekers create https://react.dev \
            --target claude \
            --max-pages 200 \
            -p standard \
            --enhance-level 0 \
            -q

      - name: Upload to Claude
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: skill-seekers upload output/react-claude.zip --target claude

      - name: Archive skill artifacts
        uses: actions/upload-artifact@v4
        with:
          name: skills-${{ github.run_number }}
          path: output/
```

## Docker

```dockerfile
FROM python:3.12-slim

RUN pip install skill-seekers

WORKDIR /skills
VOLUME /skills/output
VOLUME /skills/configs

ENTRYPOINT ["skill-seekers"]
```

Usage:
```bash
# Build
docker build -t skill-seekers .

# Create a skill
docker run -v $(pwd)/output:/skills/output \
  skill-seekers create https://react.dev --target claude -o /skills/output/react

# With API key for enhancement
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/output:/skills/output \
  skill-seekers create https://react.dev --target claude --enhance-workflow default
```

## Batch Processing

Process multiple skills in a script:

```bash
#!/bin/bash
set -e

SKILLS=(
  "https://react.dev|react|200"
  "https://vuejs.org|vue|150"
  "https://docs.djangoproject.com|django|300"
  "https://fastapi.tiangolo.com|fastapi|150"
)

for entry in "${SKILLS[@]}"; do
  IFS='|' read -r url name pages <<< "$entry"
  echo "Creating skill: $name ($pages pages)"
  skill-seekers create "$url" \
    --name "$name" \
    --target claude \
    --max-pages "$pages" \
    -p standard \
    -q
done

echo "All skills created in output/"
```

## Batch Enhancement with Background Mode

```bash
#!/bin/bash
SKILLS=("react" "vue" "django" "fastapi")

# Start all enhancements in background
for skill in "${SKILLS[@]}"; do
  echo "Starting: $skill"
  skill-seekers enhance "output/$skill/" --background
done

echo "All enhancements started. Checking status..."

# Poll until all complete
while true; do
  all_done=true
  for skill in "${SKILLS[@]}"; do
    status=$(skill-seekers enhance-status "output/$skill/" --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    if [ "$status" != "completed" ] && [ "$status" != "failed" ]; then
      all_done=false
      echo "  $skill: $status"
    else
      echo "  $skill: $status"
    fi
  done
  if $all_done; then break; fi
  sleep 10
done
```

## Incremental Updates

Keep skills fresh without full rescrapes:

```bash
# Check what changed
skill-seekers update output/react/ --check-changes

# Apply updates
skill-seekers update output/react/

# Force update everything
skill-seekers update output/react/ --force
```

## Skill Quality Gate

Enforce quality thresholds before deployment:

```bash
#!/bin/bash
THRESHOLD=7

skill-seekers quality output/react/ --threshold $THRESHOLD --report
if [ $? -ne 0 ]; then
  echo "Quality below threshold ($THRESHOLD). Running enhancement..."
  skill-seekers enhance output/react/ --enhance-workflow default
  skill-seekers quality output/react/ --threshold $THRESHOLD
fi
```

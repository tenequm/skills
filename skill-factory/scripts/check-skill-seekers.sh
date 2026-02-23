#!/bin/bash
# Check if Skill_Seekers is installed and working

SEEKERS_PATH="${SKILL_SEEKERS_PATH:-$HOME/Skill_Seekers}"

if [ ! -d "$SEEKERS_PATH" ]; then
    echo "❌ Skill_Seekers not found at $SEEKERS_PATH"
    echo ""
    echo "Install with: $( cd "$(dirname "$0")" && pwd )/install-skill-seekers.sh"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check dependencies
cd "$SEEKERS_PATH"
if python3 -c "import cli.doc_scraper" 2>/dev/null; then
    echo "✅ Skill_Seekers installed and working"
    echo "   Location: $SEEKERS_PATH"
    exit 0
else
    echo "⚠️  Skill_Seekers found but dependencies missing"
    echo "   Fix: cd $SEEKERS_PATH && pip3 install -r requirements.txt"
    exit 1
fi

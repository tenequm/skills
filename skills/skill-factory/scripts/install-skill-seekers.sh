#!/bin/bash
# One-command Skill_Seekers installation for skill-factory

set -e

INSTALL_DIR="${SKILL_SEEKERS_PATH:-$HOME/Skill_Seekers}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Skill_Seekers Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Install location: $INSTALL_DIR"
echo ""

# Check if already installed
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Skill_Seekers already exists at $INSTALL_DIR"
    echo ""
    echo "Options:"
    echo "  1. Update existing installation"
    echo "  2. Reinstall (delete and clone fresh)"
    echo "  3. Cancel"
    echo ""
    read -p "Choice (1-3): " choice

    case $choice in
        1)
            echo "📥 Updating..."
            cd "$INSTALL_DIR"
            git pull
            ;;
        2)
            echo "🗑️  Removing old installation..."
            rm -rf "$INSTALL_DIR"
            echo "📥 Cloning fresh copy..."
            git clone https://github.com/yusufkaraaslan/Skill_Seekers "$INSTALL_DIR"
            ;;
        3)
            echo "❌ Cancelled"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo "📥 Cloning Skill_Seekers..."
    git clone https://github.com/yusufkaraaslan/Skill_Seekers "$INSTALL_DIR"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd "$INSTALL_DIR"

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt
else
    echo "❌ pip not found. Please install Python 3.10+ with pip"
    exit 1
fi

# Optional: Setup MCP if Claude Code detected
echo ""
if command -v claude &> /dev/null; then
    echo "Claude Code detected."
    read -p "Install MCP integration? (y/n): " install_mcp

    if [[ "$install_mcp" =~ ^[Yy]$ ]]; then
        if [ -f "./setup_mcp.sh" ]; then
            ./setup_mcp.sh
        else
            echo "⚠️  setup_mcp.sh not found, skipping MCP setup"
        fi
    fi
fi

# Verify installation
echo ""
echo "✅ Verifying installation..."
if python3 -c "import cli.doc_scraper" 2>/dev/null; then
    echo "✅ Skill_Seekers installed successfully!"
else
    echo "⚠️  Installation complete but verification failed"
    echo "   Try manually: cd $INSTALL_DIR && python3 -c 'import cli.doc_scraper'"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Set environment variable (optional):"
echo "  export SKILL_SEEKERS_PATH=$INSTALL_DIR"
echo ""
echo "Test installation:"
echo "  cd $INSTALL_DIR && python3 cli/doc_scraper.py --help"
echo ""
echo "Ready to use in skill-factory!"

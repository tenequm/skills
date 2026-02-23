# Skill Factory

**Autonomous skill creation agent - just describe what you need, get production-ready skills automatically.**

## What This Does

skill-factory analyzes your request, automatically selects the best creation method (documentation scraping, manual TDD, or hybrid), ensures quality compliance (score >= 8.0/10), and delivers ready-to-use skills without requiring any decision-making from you.

**Zero decision fatigue. Guaranteed quality. Just results.**

## Quick Start

```
"Create a skill for Anchor development with latest docs and best practices"
"Create a React skill from react.dev with comprehensive examples"
"Create a skill for Solana transaction debugging"
```

skill-factory will:
1. ✅ Analyze your request automatically
2. ✅ Select optimal creation method
3. ✅ Create the skill
4. ✅ Run quality loops (until score >= 8.0)
5. ✅ Test automatically
6. ✅ Deliver production-ready skill

## Features

- **Autonomous operation** - No tool selection, no navigation, no manual quality checks
- **Multi-source support** - Documentation, GitHub repos, PDFs, custom workflows
- **Quality guarantee** - Every skill scores >= 8.0/10 on Anthropic best practices
- **Automatic testing** - Generated test scenarios verify skill works
- **Integration scripts** - One-command Skill_Seekers installation and management

## Installation

```bash
# Install to Claude Code
cp -r skill/ ~/.claude/skills/skill-factory/

# Or use as plugin (if in marketplace)
/plugin install skill-factory@tenequm-plugins
```

### Optional: Install Skill_Seekers

For documentation-based skills (automatic on first use):

```bash
./scripts/install-skill-seekers.sh
```

## How It Works

### Three Paths (Automatically Selected)

**Path A: Automated (Skill_Seekers)**
- Detected: Documentation URL, GitHub repo, PDF
- Method: Scrape → Quality check → Enhance → Test → Deliver
- Time: 15-45 minutes

**Path B: Manual TDD**
- Detected: Custom workflow, no documentation source
- Method: Test-driven documentation (obra methodology)
- Time: 2-4 hours

**Path C: Hybrid**
- Detected: Documentation + custom requirements
- Method: Scrape → Add custom content → Unify → Test
- Time: 1-3 hours

You never see this complexity - skill-factory chooses automatically.

## Quality Assurance

Every delivered skill meets:
- ✅ Score >= 8.0/10 (Anthropic best practices)
- ✅ Has concrete examples (not abstract)
- ✅ Follows structure conventions
- ✅ Tested with auto-generated scenarios
- ✅ Ready to use immediately

If quality < 8.0, skill-factory keeps enhancing until it reaches threshold.

## Examples

**Documentation skill:**
```
Request: "Create React skill from react.dev"
Time: 25 minutes
Result: 8.6/10 quality, 12 examples, 347 lines
```

**Custom workflow:**
```
Request: "Create skill for debugging Solana transactions"
Time: 2.5 hours
Result: 8.3/10 quality, TDD-tested, bulletproof
```

**Hybrid:**
```
Request: "Anchor docs plus custom debugging workflows"
Time: 1.5 hours
Result: 8.9/10 quality, comprehensive coverage
```

## Architecture

```
skill-factory/
├── skill/
│   ├── SKILL.md                      # Main autonomous agent
│   ├── references/                   # Deep-dive docs
│   │   ├── request-analysis.md       # How requests parsed
│   │   ├── quality-loops.md          # Enhancement algorithms
│   │   ├── anthropic-best-practices.md
│   │   ├── obra-tdd-methodology.md
│   │   └── skill-seekers-integration.md
│   ├── scripts/                      # Integration automation
│   │   ├── install-skill-seekers.sh
│   │   ├── check-skill-seekers.sh
│   │   └── quality-check.py
│   └── examples/                     # Real-world walkthroughs
├── package.json
├── CHANGELOG.md
└── README.md
```

## Dependencies

**Required:**
- Python 3.10+ (for quality scripts)
- bash (for automation)

**Optional (auto-installed when needed):**
- [Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) (for documentation scraping)

## Credits

Built on excellent tools:
- [Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) (3,562★) - Documentation scraping
- [obra/superpowers-skills](https://github.com/obra/superpowers-skills) (417★) - TDD methodology
- [Anthropic skill-creator](https://github.com/anthropics/skills) - Best practices

skill-factory orchestrates these with automatic quality assurance.

## Philosophy

**You don't want to:**
- Navigate decision trees
- Choose between tools
- Check quality manually
- Wonder if output is good

**You want to:**
- Describe what you need
- Get high-quality result
- Start using immediately

**That's what skill-factory delivers.**

## License

MIT

## Version

0.1.0 (initial development release)

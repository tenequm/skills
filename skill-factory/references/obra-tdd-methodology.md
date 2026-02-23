# Test-Driven Documentation (TDD for Skills)

Extracted from obra/superpowers-skills with attribution.

## Core Concept

**Writing skills IS Test-Driven Development applied to process documentation.**

Test skills with subagents BEFORE writing, iterate until bulletproof.

## TDD Mapping

| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | Skill document (SKILL.md) |
| Test fails (RED) | Agent violates rule without skill |
| Test passes (GREEN) | Agent complies with skill present |
| Refactor | Close loopholes while maintaining compliance |

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

No exceptions:
- Not for "simple additions"
- Not for "just documentation updates"
- Delete untested changes and start over

## RED-GREEN-REFACTOR Cycle

### RED Phase: Write Failing Test

1. **Create pressure scenarios** with subagent
   - Combine multiple pressures (time + sunk cost + authority)
   - Make it HARD to follow the rule

2. **Run WITHOUT skill** - Document exact behavior:
   - What choices did agent make?
   - What rationalizations used? (verbatim quotes)
   - Which pressures triggered violations?

3. **Identify patterns** in failures

### GREEN Phase: Write Minimal Skill

1. **Address specific baseline failures** found in RED
   - Don't add hypothetical content
   - Write only what fixes observed violations

2. **Run WITH skill** - Agent should now comply

3. **Verify compliance** under same pressure

### REFACTOR Phase: Close Loopholes

1. **Find new rationalizations** - Agent found workaround?

2. **Add explicit counters** to skill

3. **Re-test** until bulletproof

## Pressure Types

### Time Pressure
- "You have 5 minutes to ship this"
- "Deadline is in 1 hour"

### Sunk Cost
- "You've already written 200 lines of code"
- "This has been in development for 3 days"

### Authority
- "Senior engineer approved this approach"
- "This is company standard"

### Exhaustion
- "You've been debugging for 4 hours"
- "This is the 10th iteration"

**Combine 2-3 pressures** for realistic scenarios.

## Bulletproofing Against Rationalization

Agents will rationalize violations. Close every loophole explicitly:

### Pattern 1: Add Explicit Forbid List

❌ Bad:
```markdown
Write tests before code.
```

✅ Good:
```markdown
Write tests before code. Delete code if written first. Start over.

**No exceptions:**
- Don't keep as "reference"
- Don't "adapt" while testing
- Don't look at it
- Delete means delete
```

### Pattern 2: Build Rationalization Table

Capture every excuse from testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "This is different because..." | It's not. Write test first. |

### Pattern 3: Create Red Flags List

```markdown
## Red Flags - STOP and Start Over

Saying any of these means you're about to violate the rule:
- "Code before test"
- "I already tested it manually"
- "Tests after achieve same purpose"
- "It's about spirit not ritual"

**All mean: Delete code. Start over with TDD.**
```

### Pattern 4: Address Spirit vs Letter

Add early in skill:

```markdown
**Violating the letter of the rules IS violating the spirit of the rules.**
```

Cuts off entire class of rationalizations.

## Testing Different Skill Types

### Discipline-Enforcing Skills
Rules/requirements (TDD, verification-before-completion)

**Test with:**
- Academic questions: Do they understand?
- Pressure scenarios: Do they comply under stress?
- Multiple pressures combined
- Identify and counter rationalizations

### Technique Skills
How-to guides (condition-based-waiting, root-cause-tracing)

**Test with:**
- Application scenarios: Can they apply correctly?
- Variation scenarios: Handle edge cases?
- Missing information tests: Instructions have gaps?

### Pattern Skills
Mental models (reducing-complexity concepts)

**Test with:**
- Recognition scenarios: Recognize when pattern applies?
- Application scenarios: Use the mental model?
- Counter-examples: Know when NOT to apply?

### Reference Skills
Documentation/APIs

**Test with:**
- Retrieval scenarios: Find the right information?
- Application scenarios: Use it correctly?
- Gap testing: Common use cases covered?

## Common Rationalization Excuses

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you ≠ clear to agents. Test it. |
| "It's just a reference" | References have gaps. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. Always. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE. |
| "Too tedious to test" | Less tedious than debugging bad skill in production. |
| "I'm confident it's good" | Overconfidence guarantees issues. Test anyway. |

## Testing Workflow

```bash
# 1. RED - Create baseline
create_pressure_scenario()
run_without_skill() > baseline.txt
document_rationalizations()

# 2. GREEN - Write skill
write_minimal_skill_addressing_baseline()
run_with_skill() > with_skill.txt
verify_compliance()

# 3. REFACTOR - Close loopholes
identify_new_rationalizations()
add_explicit_counters_to_skill()
rerun_tests()
repeat_until_bulletproof()
```

## Real Example: TDD Skill for Skills

When creating the writing-skills skill itself:

**RED:**
- Ran scenario: "Create a simple condition-waiting skill"
- Without TDD skill: Agent wrote skill without testing
- Rationalization: "It's simple enough, testing would be overkill"

**GREEN:**
- Wrote skill with Iron Law and rationalization table
- Re-ran scenario with skill present
- Agent now creates test scenarios first

**REFACTOR:**
- New rationalization: "I'll test after since it's just documentation"
- Added explicit counter: "Tests after = what does this do? Tests first = what SHOULD this do?"
- Re-tested: Agent complies

## Deployment Checklist

For EACH skill (no batching):

**RED Phase:**
- [ ] Created pressure scenarios (3+ combined pressures)
- [ ] Ran WITHOUT skill - documented verbatim behavior
- [ ] Identified rationalization patterns

**GREEN Phase:**
- [ ] Wrote minimal skill addressing baseline failures
- [ ] Ran WITH skill - verified compliance

**REFACTOR Phase:**
- [ ] Identified NEW rationalizations
- [ ] Added explicit counters
- [ ] Built rationalization table
- [ ] Created red flags list
- [ ] Re-tested until bulletproof

**Quality:**
- [ ] Follows Anthropic best practices
- [ ] Has concrete examples
- [ ] Quick reference table included

**Deploy:**
- [ ] Committed to git
- [ ] Tested in production conversation

## Key Insights

1. **Test BEFORE writing** - Only way to know skill teaches right thing
2. **Pressure scenarios required** - Agents need stress to reveal rationalizations
3. **Explicit > Implicit** - Close every loophole with explicit forbid
4. **Iterate** - First version never bulletproof, refactor until it is
5. **Same rigor as code** - Skills are infrastructure, test like code

## Source

Based on [obra/superpowers-skills](https://github.com/obra/superpowers-skills)
- skills/meta/writing-skills/SKILL.md
- TDD methodology applied to documentation

## Quick TDD Checklist

Before deploying any skill:
- [ ] Created and documented failing baseline test?
- [ ] Skill addresses specific observed violations?
- [ ] Tested with skill present - passes?
- [ ] Identified and countered rationalizations?
- [ ] Explicit forbid list included?
- [ ] Red flags section present?
- [ ] Re-tested until bulletproof?

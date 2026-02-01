# Product Vision - Swanson Framework

## What This Is

An **autonomous development framework** that takes well-formed PRDs and delivers working, tested software without human intervention. Built on Ron Swanson's philosophy: "Never half-ass two things. Whole-ass one thing."

## Who It's For

**Primary User:** Engineering leaders who need to accelerate delivery by automating routine development work.

**Use Case:** Queue up 3-5 PRDs before bed, wake up to working features with passing tests.

## Success Criteria

**v1 is successful when:**
1. Can execute ONE PRD end-to-end (tests generated → feature built → tests pass)
2. Can execute MULTIPLE PRDs sequentially overnight
3. Blocks on test failures (doesn't claim success when tests fail)
4. Maintains clean state (knows where it left off, can resume)
5. Costs are predictable (~$0.14 per story with Sonnet)

**v1 is NOT about:**
- Cost optimization (accept Sonnet everywhere)
- Advanced features (learnings, self-healing, integrations)
- Enterprise scale (single developer workflow first)

## Core Principles

### 1. External Validation
- Tests are written BEFORE code (ATDD)
- pytest validates success, not Claude's claims
- Loop enforces passing tests before marking stories complete
- No story completes without provable test results

### 2. Simplicity Over Sophistication
- One model (Sonnet) for everything in v1
- Fixed-size state (state.json), not growing logs
- No "smart" features that add complexity
- Ship working tool, optimize later with data

### 3. Strict Contracts
- Engine only accepts PRDs matching schema
- Engine only emits status updates
- No external integrations inside the loop
- Clear boundaries = protected purity

### 4. Fail Loudly
- Block on test failures
- Block on malformed PRDs
- Block on missing dependencies
- Show failure details, don't swallow errors

## What The Framework IS

**The Core Loop:**
```
1. Read state (where did we leave off?)
2. Pick next story from queue
3. Generate tests from acceptance criteria
4. Verify tests fail (feature doesn't exist yet)
5. Implement feature to pass tests
6. Verify tests pass (feature works)
7. Update state (mark story complete)
8. Append to history (audit trail)
9. Git commit (working increment)
10. Repeat until queue empty
```

**Components:**
- `loop.py` - Main orchestration (bash)
- `context_loader.py` - Loads relevant docs for Claude Code sessions
- `signal_detector.py` - Detects completion/failure signals
- `executor.py` - Invokes Claude Code with right context
- `state.json` - Current execution state
- `history.md` - Append-only audit trail

## What The Framework IS NOT

### ❌ Not a Code Generator
It's not a tool that "writes code for you." It's an automation engine that executes well-defined work items.

### ❌ Not an AI Pair Programmer
It doesn't help you write code interactively. It autonomously executes queued work while you sleep.

### ❌ Not a Test Framework
It uses pytest. It generates tests from AC, but relies on standard Python testing tools.

### ❌ Not a Planning Tool
It executes PRDs, it doesn't create them. PRDs are created by humans or by separate tools (like FADE PRD Generator).

### ❌ Not Self-Healing
If tests fail, it blocks and reports failure. It does NOT attempt to fix itself.

### ❌ Not Integrated
It doesn't talk to JIRA, Slack, GitHub Issues, etc. It reads from `prds/` directory and writes to `state.json` and `history.md`.

### ❌ Not Learning
It doesn't maintain a learnings database. Knowledge goes in code (via comments) or in standards (via documentation).

## Architectural Boundaries

### Input Boundary
**Accepts:** JSON files in `prds/` directory matching PRD schema
**Rejects:** Malformed PRDs, PRDs without AC, PRDs with invalid types

### Output Boundary
**Emits:** 
- Updated `state.json` (current position)
- Appended `history.md` (audit trail)
- Git commits (working increments)
- Test results (pytest output)

**Does NOT emit:**
- API calls to external systems
- Database writes (except application code)
- File system writes outside repo

### Dependency Boundary
**Depends on:**
- Claude Code CLI (for execution)
- pytest (for test running)
- Git (for commits)
- Python 3.12+ (for orchestration and scripts)
- Cross-platform shell (bash on macOS/Linux, PowerShell on Windows)
- Windows 11+ (for Windows users)
- macOS 13+ (Ventura or later, for macOS users)

**Does NOT depend on:**
- Anthropic API directly (uses Claude Code, not API)
- External databases
- External services
- GUI frameworks
- macOS-specific tools (must work on Windows too)

## Quality Standards

### Code Quality
- All code must pass tests before story completion
- Tests must be generated from acceptance criteria
- No stubbed tests allowed
- pytest exit code 0 = success, non-zero = failure

### State Management
- state.json is the single source of truth for current position
- Never infer state from git history or file contents
- Always update state.json before marking work complete

### Error Handling
- All errors must be visible to the user
- No swallowed exceptions
- No silent failures
- Block execution on errors, don't continue

### Git Hygiene
- One commit per story completion
- Conventional commit format: `feat:`, `fix:`, `chore:`, etc.
- Commit message includes story ID: `feat: implement login endpoint (US-002)`

## Non-Goals (For v1)

**Cost Optimization:**
- Not selecting cheapest model per task
- Not caching context between sessions
- Accept Sonnet costs, optimize later with data

**Advanced Features:**
- No learnings.md (knowledge in code/standards)
- No self-healing (too dangerous)
- No integrations (keep pure)
- No progress estimation
- No parallel execution

**Enterprise Features:**
- No multi-user support
- No role-based access
- No audit logs beyond history.md
- No webhook notifications

**Quality Metrics:**
- No test coverage tracking
- No code complexity analysis
- No performance monitoring

## Future Vision (Post-v1)

### Phase 1: Brownfield Rescue Mode

**The Problem:**
Most enterprise codebases are brownfield - legacy code, tech debt, inconsistent patterns. Traditional "AI coding assistants" multiply developer output (good or bad), which accelerates failure on brownfield projects. A bad developer with 10x productivity creates 10x liability.

**The Solution:**
Systematic tech debt cleanup BEFORE feature velocity. Use the engine's standards enforcement to transform brownfield → gold standard.

**How it works:**
1. **Stabilization Phase** (Week 1)
   - Audit codebase, identify anti-patterns
   - Document "good" in `standards.md`
   - Create tech-debt PRD queue (20-30 items)

2. **Cleanup Phase** (Week 2-4)
   - Queue tech-debt PRDs: "Replace plaintext passwords", "Add input validation", "Extract duplicated logic"
   - Engine executes overnight with standards enforcement
   - ATDD ensures fixes work, don't break existing functionality
   - Cost: ~$0.14/story = predictable, cheap transformation

3. **Feature Velocity Phase** (Week 5+)
   - Codebase now at gold standard
   - New features built with quality enforced
   - Sustainable velocity maintained

**Example Tech-Debt PRDs:**
```json
{
  "type": "tech-debt",
  "name": "Fix Authentication Security",
  "description": "Replace plaintext password storage with bcrypt hashing",
  "userStories": [
    {
      "id": "US-001",
      "title": "Migrate existing passwords to bcrypt",
      "acceptanceCriteria": [
        "All passwords migrated to bcrypt (cost factor 12)",
        "Migration script tested on production data copy",
        "Old plaintext code removed",
        "All tests pass after migration"
      ]
    }
  ]
}
```

**Key Insight:**
Standards enforcement + ATDD = Quality multiplier, not chaos multiplier. Unlike tools that assume developer competence, this enforces quality regardless of input.

**Design Principle:**
Nothing in v1 should block brownfield rescue. Specifically:
- PRD schema supports `tech-debt` type (even if not used in v1)
- Standards mechanism works for any codebase (not just greenfield)
- ATDD works for refactoring (not just new features)
- State management supports any PRD type

---

### Phase 2: Cost Optimization

**After brownfield rescue proves valuable:**
- Multi-model orchestration (Haiku for git, Opus for complex work)
- Just-in-time standards loading (semantic search for relevant sections)
- Parallel story execution (multiple Claude Code sessions)

---

### Phase 3: Enterprise Scale

**After cost optimization proves ROI:**
- Integration touchpoints (JIRA sync, Slack notifications)
- Multi-project orchestration
- Shared learnings across teams
- Dashboard for executive visibility

---

**The Rule:**
Ship v1 minimal. Validate with real brownfield projects. Let data guide what Phase 1/2/3 actually need.

**But ensure v1 architecture doesn't block the vision.**

## Success Metrics

**For v1 to ship:**
- ✅ Execute 1 PRD with 3 stories, all tests pass
- ✅ Execute 5 PRDs overnight, wake to working software
- ✅ Gracefully handle 1 test failure (blocks, shows details)
- ✅ Resume from interruption (read state.json, continue)
- ✅ Predictable cost (can estimate dollars per story)

**When v1 is ready for v2:**
- 50+ PRDs executed successfully
- Data on where token costs concentrate
- Evidence that specific optimizations would help
- User feedback on what hurts vs what works

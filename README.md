# Swanson Framework

**Autonomous development framework for organizational transformation through quality-enforced code execution.**

> "Never half-ass two things. Whole-ass one thing." - Ron Swanson

## What Is Swanson?

Swanson is NOT a coding assistant. It's a framework for systematic codebase transformation through Acceptance Test-Driven Development (ATDD).

**The Problem:** Most AI coding tools multiply developer output (good OR bad). A bad developer with 10x productivity = 10x liability.

**Swanson's Solution:** Standards enforcement + external test validation = Quality multiplier, not chaos multiplier.

### How It Works

1. **Queue-driven execution** - PRDs in `prds/queue/`, processed sequentially
2. **Test-first enforcement** - Acceptance criteria → tests → implementation
3. **External validation** - Tests generated and verified in separate sessions (prevents AI from falsifying results)
4. **Standards compliance** - Organizational coding standards loaded every session
5. **Predictable cost** - ~$0.14 per user story (Sonnet 4.5)

### The Vision: Brownfield Rescue

The killer use case (Phase 1, future):
- Audit existing codebase, identify anti-patterns
- Document "good" in `standards.md`
- Create 20-30 tech-debt PRDs (systematic cleanup)
- Queue them, run overnight (~$4-7 total)
- Wake to transformed codebase (brownfield → silver standard)

**v1 doesn't build this yet, but the architecture supports it.**

## Installation

### Prerequisites
- Python 3.12+
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Anthropic API key or Claude Code OAuth

### Install Swanson

```bash
pip install swanson
```

Or from source:
```bash
git clone https://github.com/themitchelli/swanson.git
cd swanson
pip install -e .
```

### Initialize a Project

```bash
cd your-project
swanson init
```

This creates:
- `.swanson/` - Configuration directory
- `.swanson/templates/` - Customizable contract documents
- `prds/queue/` - Work queue directory

### Configure

Edit `.swanson/config.json`:
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_retries": 3,
  "test_timeout": 300,
  "project_root": "."
}
```

## Quick Start

### 1. Create a PRD

Create `prds/queue/example.json`:
```json
{
  "id": "FEAT-001",
  "title": "Add user authentication",
  "type": "feature",
  "userStories": [
    {
      "id": "US-001",
      "title": "User can register with email/password",
      "acceptanceCriteria": [
        "Registration endpoint accepts email and password",
        "Password is hashed with bcrypt (cost factor 12)",
        "Valid registration returns 201 Created with user ID",
        "Duplicate email returns 409 Conflict"
      ]
    }
  ]
}
```

### 2. Run Swanson

```bash
swanson run
```

Swanson will:
1. Pick `example.json` from queue
2. Generate tests from acceptance criteria
3. Verify tests fail (feature doesn't exist)
4. Implement feature to pass tests
5. Verify tests pass
6. Move PRD to `prds/completed/`
7. Update `state.json` and `history.md`

### 3. Review Output

- **Tests:** Generated in your test directory
- **Code:** Implemented in your source directory
- **History:** Audit trail in `history.md`
- **State:** Current execution state in `state.json`

## Platform Support

- **macOS:** Fully tested
- **Windows:** Validated via CI, not manually tested
- **Linux:** Should work (not tested)

Cross-platform support via Python 3.12+ and pathlib.

## Project Structure

```
your-project/
├── .swanson/
│   ├── config.json           # Configuration
│   └── templates/            # Contract documents
│       ├── product-vision.md
│       ├── standards.md
│       ├── context-map.md
│       ├── prd-schema.md
│       └── BUILD.md
├── prds/
│   ├── queue/                # Work to do
│   ├── completed/            # Finished work
│   └── expedite/             # Urgent items (future)
├── state.json                # Execution state
└── history.md                # Audit trail
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Contributing

This is a personal project (for now). If you want to contribute:
1. Fork the repo
2. Create a feature branch
3. Submit a PR with clear description

### License

MIT License - See LICENSE file

## FAQ

**Q: Why ATDD? Why not just let AI write code?**
A: Because AI will happily write tests that pass for broken code. External validation (separate sessions) prevents this.

**Q: Why so slow? One story takes ~5 minutes.**
A: We're optimizing for organizational transformation, not developer speed. Slower to execute, faster to production-quality code (no rework cycles).

**Q: What if a test fails?**
A: Swanson stops, shows the failure details, and waits. You fix the PRD or standards, then resume. Fail loudly > silent corruption.

**Q: Can I use this for greenfield projects?**
A: Yes, but the real value is brownfield rescue (Phase 1). Systematic tech debt cleanup is the killer use case.

**Q: What's the cost?**
A: ~$0.14 per user story (Sonnet 4.5). Predictable and measurable.

## Roadmap

- **v1 (current):** Core loop, ATDD enforcement, cross-platform support
- **v2:** Cost optimization (Haiku for tests, Sonnet for implementation)
- **Phase 1:** Brownfield rescue mode (systematic tech debt cleanup)
- **Phase 2:** Enterprise integrations (JIRA, Azure DevOps, Slack)
- **Phase 3:** Multi-repo orchestration

## Credits

Built by Steve Mitchelli ([@themitchelli](https://github.com/themitchelli))

Inspired by FADE and MADeIT (RIP). Powered by Claude Code and Anthropic API.

---

**"Never half-ass two things. Whole-ass one thing."** - Ron Swanson

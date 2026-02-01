# Context Map - Swanson Framework

## Purpose
This document serves as the entry point for Claude Code sessions working on Swanson. It explains what documents exist, what they contain, and when to read them.

---

## Document Structure

```
/
├── context-map.md          ← YOU ARE HERE (read first)
├── product-vision.md       ← Strategic direction and boundaries
├── standards.md            ← Code quality expectations
├── prd-schema.md           ← PRD format specification
├── BUILD.md                ← Build instructions for Swanson
│
├── state.json              ← Current execution state (read on startup)
├── history.md              ← Audit trail (append only, never read)
│
├── prds/                   ← Work queue
│   ├── 001-FEAT-*.json
│   ├── 002-BUG-*.json
│   └── ...
│
├── src/swanson/            ← Framework code (you will build this)
└── tests/                  ← Generated tests (you will create these)
```

---

## Reading Order for Claude Code

### On First Session (Building the Engine)
1. **This file** (`context-map.md`) - Understand the layout
2. `product-vision.md` - Understand what you're building and why
3. `BUILD.md` - Follow the exact build specification
4. `prd-schema.md` - Understand PRD format (for context loading logic)
5. `standards.md` - Understand quality expectations

**Task:** Build the engine exactly as specified in BUILD.md. Nothing more, nothing less.

---

### On Execution Sessions (Running Stories)

#### Session Type 1: Test Generation
**When:** First session for a new story

**Read in this order:**
1. `state.json` - Know which story you're working on
2. `prds/XXX-*.json` - Read the current PRD
3. `prd-schema.md` - Understand AC structure
4. `standards.md` - Sections: Testing Standards, Code Quality

**Task:** 
- Generate pytest tests from acceptance criteria
- One test per AC (minimum)
- Follow AAA pattern (Arrange, Act, Assert)
- Include NFR tests (performance, security, etc.)
- Save to `tests/test_<story_id>.py`

**Do NOT:**
- Implement any features
- Stub tests (all tests must have real assertions)
- Skip any acceptance criteria

---

#### Session Type 2: Implementation
**When:** Second session for a story (after tests are generated)

**Read in this order:**
1. `state.json` - Know which story you're working on
2. `prds/XXX-*.json` - Read the current PRD
3. `tests/test_<story_id>.py` - Read the failing tests you must pass
4. `standards.md` - All sections (full quality expectations)
5. Existing `src/` code - Understand current implementation

**Task:**
- Implement features to make tests pass
- Follow all standards
- Write clean, documented code
- Handle errors gracefully

**Do NOT:**
- Modify tests to make them pass (tests are the contract)
- Skip any acceptance criteria
- Add features not in the PRD
- Ignore standards

---

## Document Descriptions

### `product-vision.md` - Strategic Direction
**Contains:**
- What Swanson does and doesn't do
- Architectural boundaries
- Core principles (external validation, simplicity, strict contracts)
- Success criteria for v1
- Future vision (brownfield rescue, cost optimization, enterprise scale)

**Read when:**
- Building Swanson (understand the why)
- Uncertain about scope (what's in vs out)
- Deciding whether to add a feature (default: don't)

---

### `standards.md` - Quality Expectations
**Contains:**
- Code quality rules (function length, complexity, naming)
- Testing standards (coverage, structure, independence)
- API conventions (REST, status codes, response format)
- Security standards (auth, validation, secrets)
- Git standards (commit messages, scope)
- Documentation requirements

**Read when:**
- Implementing features (follow all standards)
- Writing tests (follow testing standards)
- Making git commits (follow commit format)

**Size:** ~3K tokens - loaded for every implementation session

---

### `prd-schema.md` - PRD Format
**Contains:**
- Required fields for PRDs
- Acceptance criteria rules
- Complexity guidelines
- Validation rules
- Complete examples

**Read when:**
- Building context loading logic (understand schema)
- Generating tests (understand AC structure)
- Validating PRDs (check schema compliance)

---

### `BUILD.md` - Build Instructions
**Contains:**
- Exact file structure to create
- Component specifications for Swanson
- ATDD flow details
- Signal protocol
- Success criteria

**Read when:**
- Building Swanson (first session only)
- Unclear about component responsibilities

---

### `state.json` - Execution State
**Contains:**
```json
{
  "current_prd": "001-FEAT-user-auth.json",
  "current_story": "US-002",
  "completed_stories": ["US-001"],
  "remaining_stories": ["US-003", "US-004"],
  "last_updated": "2026-02-01T19:30:00Z"
}
```

**Read when:**
- Starting any execution session (know where you left off)
- Resuming after interruption

**Update when:**
- Story completes (move story from remaining to completed)
- All stories complete (move to next PRD)

---

### `history.md` - Audit Trail
**Contains:**
- Chronological log of story completions
- Test results
- Commit hashes
- Duration, timestamps

**Never read this file.** It's for human diagnosis only.

**Always append to this file** when a story completes.

---

## Loading Strategy

### For Engine Build (First Session)
Load everything:
- context-map.md (this file)
- product-vision.md (~2K tokens)
- BUILD.md (~3K tokens)
- prd-schema.md (~1.5K tokens)
- standards.md (~3K tokens)

**Total:** ~9.5K tokens - acceptable for one-time build session

---

### For Test Generation Sessions
Load only what's needed:
- state.json (~0.2K tokens)
- Current PRD (~1K tokens)
- prd-schema.md (~1.5K tokens)
- standards.md - Testing sections only (~1K tokens)

**Total:** ~3.7K tokens - minimal, focused

---

### For Implementation Sessions
Load comprehensively:
- state.json (~0.2K tokens)
- Current PRD (~1K tokens)
- Generated tests (~1K tokens)
- standards.md - Full doc (~3K tokens)
- Existing code (~2-5K tokens, varies)

**Total:** ~7-10K tokens - acceptable for quality work

---

## Key Principles

### 1. Context-Map is Your Entry Point
Always start here. This document tells you what to read next.

### 2. Standards Apply to Everything
Every line of code, every test, every commit must follow standards.md.

### 3. State is Truth
state.json tells you where you are. Trust it, update it, never infer it.

### 4. Tests Define Done
If tests don't pass, story isn't done. No exceptions.

### 5. History is Write-Only
Append to history.md, never read it. It's for humans, not for you.

---

## Common Scenarios

### "I'm starting a new test generation session"
1. Read context-map.md (this file)
2. Read state.json (know which story)
3. Read the PRD (understand requirements)
4. Read prd-schema.md (understand AC structure)
5. Read standards.md - Testing sections
6. Generate tests
7. Update state.json (mark tests generated)

### "I'm starting an implementation session"
1. Read context-map.md (this file)
2. Read state.json (know which story)
3. Read the PRD (understand requirements)
4. Read the generated tests (understand what must pass)
5. Read standards.md (full document)
6. Read existing code (understand current state)
7. Implement features
8. Update state.json (mark story complete if tests pass)

### "I'm building Swanson for the first time"
1. Read context-map.md (this file)
2. Read product-vision.md (understand goals)
3. Read BUILD.md (exact specifications)
4. Read prd-schema.md (for context loading logic)
5. Read standards.md (quality expectations)
6. Build exactly what BUILD.md specifies
7. Do NOT add extra features

### "I'm unsure if I should add a feature"
1. Check product-vision.md - "What The Engine IS NOT"
2. Check BUILD.md - Is it specified?
3. Default answer: **NO**, don't add it
4. If BUILD.md doesn't mention it, don't build it

---

## Error Handling

### If you encounter a conflict between documents
1. **Stop immediately**
2. Report the conflict clearly
3. Block execution
4. Wait for human clarification

Example conflicts:
- AC requires plaintext passwords vs standards require bcrypt
- PRD asks for feature that product-vision explicitly excludes
- BUILD.md specifies component that violates standards

### If you can't find a required document
1. List what you were looking for
2. List what documents exist
3. Block execution
4. Wait for human to add missing document

### If a PRD is malformed
1. List specific schema violations
2. Reference prd-schema.md requirements
3. Block execution
4. Wait for human to fix PRD

---

## Success Indicators

You're doing it right when:
- ✅ You read documents in the specified order
- ✅ You follow standards for every line of code
- ✅ You generate real tests, not stubs
- ✅ You block on errors instead of guessing
- ✅ You update state.json after each story
- ✅ You append to history.md with details
- ✅ You only build what's specified in BUILD.md

You're doing it wrong when:
- ❌ You skip reading standards
- ❌ You stub tests instead of implementing them
- ❌ You mark stories complete when tests fail
- ❌ You add features not in BUILD.md or PRD
- ❌ You guess instead of blocking on errors
- ❌ You read history.md during execution
- ❌ You modify state.json without completing work

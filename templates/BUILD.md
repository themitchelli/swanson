# BUILD Specification - Swanson Framework

## Purpose
This document specifies EXACTLY what to build for the Swanson autonomous development framework. Build what's specified here. Nothing more, nothing less.

**Philosophy:** "Never half-ass two things. Whole-ass one thing." - Ron Swanson

---

## Success Criteria

**v1 is complete when:**
1. ✅ All components below are implemented
2. ✅ Can execute ONE PRD with 3 stories end-to-end
3. ✅ Tests are generated before implementation (ATDD)
4. ✅ Tests must pass before story marked complete
5. ✅ State persists between sessions (can resume)
6. ✅ History tracks all completions

---

## File Structure to Create

```
/
├── src/
│   └── swanson/
│       ├── __init__.py
│       ├── loop.py              # Main orchestration (Python, cross-platform)
│       ├── context_loader.py    # Loads relevant docs for sessions
│       ├── signal_detector.py   # Detects completion signals
│       ├── executor.py          # Invokes Claude Code sessions
│       ├── state_manager.py     # Manages state.json
│       ├── history_logger.py    # Appends to history.md
│       └── config.py            # Configuration management
│
├── templates/                   # Default templates for .swanson/
│   ├── product-vision.md
│   ├── standards.md
│   ├── context-map.md
│   └── prd-schema.md
│
├── tests/                       # Generated tests go here
│   └── .gitkeep
│
├── prds/                        # PRD queue
│   └── .gitkeep
│
├── .env.template
├── config.example.json
├── state.json                   # Execution state (created on first run)
├── history.md                   # Audit trail (created on first run)
├── setup.py                     # Interactive setup script
├── init.py                      # Project initialization
└── README.md                    # Usage instructions
```

**CRITICAL: Cross-Platform Requirement**

The framework MUST work on:
- macOS (development)
- Windows (production users)
- Linux (optional, nice to have)

**This means:**
- NO bash scripts (use Python for orchestration)
- NO Unix-specific tools (awk, sed, grep)
- NO macOS-specific paths (/Users/, .bash_profile)
- Use `pathlib.Path` for all file paths
- Use `subprocess.run()` for shell commands
- Test on both macOS and Windows before shipping

---

## Component Specifications

### 1. `loop.py` - Main Orchestration

**Responsibility:** Control flow for ATDD process (Python for cross-platform)

**Behavior:**
```python
#!/usr/bin/env python3
"""
ATDD Loop - Cross-Platform Orchestration
Works on macOS, Windows, and Linux
"""

import subprocess
import sys
from pathlib import Path
from swanson.state_manager import StateManager
from swanson.executor import Executor
from swanson.history_logger import HistoryLogger

def main():
    """
    ATDD Loop:
    1. Read state - which PRD/story are we on?
    2. For each story in current PRD:
       a. Test Generation Session (if tests don't exist)
       b. Verify tests fail (expected state)
       c. Implementation Session
       d. Verify tests pass (required for completion)
       e. Update state
       f. Append to history
       g. Git commit
    3. Move to next PRD or exit
    """
    
    state = StateManager()
    executor = Executor()
    history = HistoryLogger()
    
    while True:
        # Read current state
        current_prd = state.get_current_prd()
        current_story = state.get_current_story()
        
        # Exit if queue empty
        if not current_prd:
            print("Queue empty. All work complete.")
            sys.exit(0)
        
        # Test Generation Phase
        test_file = Path(f"tests/test_{current_story}.py")
        if not test_file.exists():
            print(f"=== Test Generation: {current_story} ===")
            success = executor.execute_test_generation(current_prd, current_story)
            
            # Verify tests exist
            if not test_file.exists():
                print(f"BLOCKED: Test generation failed for {current_story}")
                sys.exit(1)
            
            # Verify tests fail (feature doesn't exist yet)
            result = subprocess.run(
                ["pytest", str(test_file)],
                capture_output=True
            )
            if result.returncode == 0:
                print("BLOCKED: Tests passing before implementation (should fail)")
                sys.exit(1)
            
            print("✓ Tests generated and failing as expected")
        
        # Implementation Phase
        print(f"=== Implementation: {current_story} ===")
        success = executor.execute_implementation(current_prd, current_story)
        
        # Verify tests pass
        result = subprocess.run(
            ["pytest", str(test_file)],
            capture_output=True
        )
        if result.returncode != 0:
            print("BLOCKED: Tests failing after implementation")
            print(result.stdout.decode())
            print(result.stderr.decode())
            sys.exit(1)
        
        print("✓ Tests passing")
        
        # Update state
        state.mark_story_complete(current_story)
        
        # Append to history
        history.log_completion(current_story, current_prd, result)
        
        # Git commit
        commit_msg = executor.generate_commit_message(current_story)
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_msg])
        
        print(f"✓ Story {current_story} complete\n")

if __name__ == "__main__":
    main()
```

**Key Cross-Platform Considerations:**
- Use `pathlib.Path` for all file paths (handles Windows/Unix differences)
- Use `subprocess.run()` instead of shell commands
- No bash-specific syntax
- Works on Windows, macOS, and Linux

---

### 2. `context_loader.py` - Context Management

**Responsibility:** Load relevant documents for each session type

**Functions:**

```python
def load_test_generation_context(prd_path: str, story_id: str) -> str:
    """
    Load context for test generation session.
    
    Returns concatenated string containing:
    - state.json
    - PRD content
    - prd-schema.md (for AC structure)
    - standards.md (Testing Standards section only)
    """
    pass

def load_implementation_context(prd_path: str, story_id: str) -> str:
    """
    Load context for implementation session.
    
    Returns concatenated string containing:
    - state.json
    - PRD content
    - Generated tests for this story
    - standards.md (full document)
    - Existing source files (if any)
    """
    pass

def extract_acceptance_criteria(prd_path: str, story_id: str) -> List[str]:
    """Extract AC list for a specific story from PRD."""
    pass
```

**Rules:**
- Always include state.json (shows current position)
- Only load relevant sections of standards for test generation
- Load full standards for implementation
- Keep total context under 15K tokens per session

---

### 3. `signal_detector.py` - Completion Detection

**Responsibility:** Parse Claude Code output for signals

**Functions:**

```python
def detect_signal(output: str) -> Tuple[str, Optional[str]]:
    """
    Parse Claude Code output for completion signals.
    
    Returns:
        (signal_type, details)
        
    Signal types:
        - "TESTS_GENERATED" - Test file created
        - "STORY_DONE" - Implementation complete
        - "BLOCKED" - Cannot proceed (details explain why)
        - "UNKNOWN" - No signal detected (error state)
    """
    pass

def extract_story_id(signal_line: str) -> str:
    """Extract story ID from signal like 'STORY_DONE: US-002'."""
    pass
```

**Signal format (in Claude Code output):**
```
TESTS_GENERATED: US-002
STORY_DONE: US-002
BLOCKED: Missing database connection string
```

---

### 4. `executor.py` - Claude Code Invocation

**Responsibility:** Execute Claude Code sessions with proper context

**Functions:**

```python
def execute_test_generation(prd_path: str, story_id: str) -> bool:
    """
    Run test generation session.
    
    1. Load test generation context
    2. Create prompt for Claude Code
    3. Execute: claude-code --model sonnet
    4. Detect TESTS_GENERATED signal
    5. Verify test file exists
    
    Returns:
        True if successful, False if blocked
    """
    pass

def execute_implementation(prd_path: str, story_id: str) -> bool:
    """
    Run implementation session.
    
    1. Load implementation context
    2. Create prompt for Claude Code
    3. Execute: claude-code --model sonnet
    4. Detect STORY_DONE signal
    5. Return success/failure
    
    Returns:
        True if successful, False if blocked
    """
    pass

def generate_commit_message(story_id: str) -> str:
    """
    Generate conventional commit message for completed story.
    
    Format: <type>: <description> (<story-id>)
    Example: feat: implement user login (US-002)
    """
    pass
```

**Prompt templates:**

Test Generation Prompt:
```
You are in Test Generation mode.

Context loaded:
{context}

Your task:
1. Read the acceptance criteria for story {story_id}
2. Generate pytest tests in tests/test_{story_id}.py
3. One test per acceptance criterion (minimum)
4. Follow AAA pattern (Arrange, Act, Assert)
5. Include NFR tests (performance, security, etc.)
6. Do NOT implement any features
7. Do NOT stub tests - all tests must have real assertions

When complete, output exactly:
TESTS_GENERATED: {story_id}
```

Implementation Prompt:
```
You are in Implementation mode.

Context loaded:
{context}

Your task:
1. Read the failing tests in tests/test_{story_id}.py
2. Implement features to make ALL tests pass
3. Follow ALL standards in standards.md
4. Write clean, documented code
5. Handle errors gracefully
6. Do NOT modify tests to make them pass

Run pytest tests/test_{story_id}.py to verify.

When all tests pass, output exactly:
STORY_DONE: {story_id}

If you cannot proceed, output:
BLOCKED: <reason>
```

---

### 5. `state_manager.py` - State Persistence

**Responsibility:** Read and update state.json

**Schema:**
```json
{
  "current_prd": "001-FEAT-user-auth.json",
  "current_story": "US-002",
  "completed_stories": ["US-001"],
  "remaining_stories": ["US-003", "US-004"],
  "last_updated": "2026-02-01T20:00:00Z",
  "session_count": 3
}
```

**Functions:**

```python
def initialize_state() -> None:
    """Create state.json if it doesn't exist."""
    pass

def get_current_prd() -> Optional[str]:
    """Return current PRD filename or None if queue empty."""
    pass

def get_current_story() -> Optional[str]:
    """Return current story ID or None."""
    pass

def mark_story_complete(story_id: str) -> None:
    """
    Move story from remaining to completed.
    If no remaining stories, archive PRD and move to next.
    """
    pass

def load_next_prd() -> None:
    """
    Archive current PRD to prds/archive/
    Load next PRD from prds/ directory
    Initialize remaining_stories from new PRD
    """
    pass

def get_remaining_stories() -> List[str]:
    """Return list of story IDs not yet completed."""
    pass
```

**Rules:**
- Always update last_updated timestamp
- Increment session_count on each session start
- Never allow state to become inconsistent
- Write atomically (temp file + rename)

---

### 6. `history_logger.py` - Audit Trail

**Responsibility:** Append to history.md

**Format:**
```markdown
## 2026-02-01 20:15 - Story US-002 Complete

- **PRD:** 001-FEAT-user-auth.json
- **Story:** US-002 - User Login
- **Duration:** 12 minutes
- **Tests:** 5/5 passed
- **Commit:** abc1234
- **Model:** Sonnet
- **Session:** 3

### Acceptance Criteria Met
- [x] POST /api/login accepts email and password
- [x] Returns 200 with JWT token on valid credentials
- [x] Returns 401 on invalid password
- [x] Returns 404 if user doesn't exist
- [x] JWT token expires after 1 hour

---
```

**Functions:**

```python
def log_completion(
    story_id: str,
    prd_path: str,
    test_results: Dict,
    commit_hash: str,
    duration_seconds: int
) -> None:
    """Append completion entry to history.md."""
    pass

def log_block(story_id: str, reason: str) -> None:
    """Append block entry to history.md."""
    pass
```

**Rules:**
- Always append, never modify existing entries
- Include timestamp in every entry
- Log both successes and blocks
- Keep entries readable (markdown formatted)

---

## ATDD Flow Specification

### Overview
```
Story → Test Generation → Verify Tests Fail → Implementation → Verify Tests Pass → Complete
```

### Phase 1: Test Generation

**Input:**
- PRD with acceptance criteria
- Story ID

**Process:**
1. Load minimal context (PRD + schema + test standards)
2. Invoke Claude Code with test generation prompt
3. Claude generates tests in `tests/test_<story_id>.py`
4. Claude outputs `TESTS_GENERATED: <story_id>`

**Output:**
- Test file exists: `tests/test_<story_id>.py`
- Tests fail when run (expected state)

**Validation:**
```bash
# Must exist
test -f "tests/test_${story_id}.py"

# Must fail (feature doesn't exist)
! pytest "tests/test_${story_id}.py"
```

**If validation fails:** BLOCK and report

---

### Phase 2: Implementation

**Input:**
- PRD with acceptance criteria
- Generated tests (failing)
- Story ID

**Process:**
1. Load full context (PRD + tests + standards + existing code)
2. Invoke Claude Code with implementation prompt
3. Claude implements features to pass tests
4. Claude runs pytest to verify
5. Claude outputs `STORY_DONE: <story_id>` OR `BLOCKED: <reason>`

**Output:**
- Feature code exists
- Tests pass when run

**Validation:**
```bash
# Must pass
pytest "tests/test_${story_id}.py"
```

**If validation fails:** BLOCK and show pytest output

---

### Phase 3: Completion

**Actions after tests pass:**
1. Update state.json (mark story complete)
2. Append to history.md (log completion)
3. Git commit (working increment)
4. Move to next story or next PRD

**Git commit format:**
```
<type>: <description> (<story-id>)

Examples:
feat: implement user login (US-002)
fix: handle missing email in registration (US-001)
```

---

## Error Handling

### Test Generation Fails
**Symptoms:**
- No test file created
- Test file is empty
- Tests are stubbed (no assertions)

**Action:**
- BLOCK with message: "Test generation failed for {story_id}"
- Show Claude Code output
- Exit loop

---

### Tests Pass Before Implementation
**Symptoms:**
- pytest exits 0 on newly generated tests
- This means tests are stubbed or feature already exists

**Action:**
- BLOCK with message: "Tests passing before implementation (should fail)"
- Show test file contents
- Exit loop

---

### Implementation Fails
**Symptoms:**
- Claude outputs `BLOCKED: <reason>`
- Tests still failing after implementation
- No signal detected

**Action:**
- BLOCK with message from Claude or pytest output
- Show failure details
- Exit loop

---

### PRD Malformed
**Symptoms:**
- Missing required fields
- Invalid JSON
- No acceptance criteria

**Action:**
- BLOCK with schema validation errors
- Reference prd-schema.md
- Exit loop

---

## Testing the Engine Itself

**After building, test with this PRD:**

```json
{
  "type": "feature",
  "name": "Health Check Endpoint",
  "description": "Add a health check endpoint for monitoring",
  "userStories": [
    {
      "id": "US-001",
      "title": "Basic Health Check",
      "description": "GET /health returns 200 OK",
      "acceptanceCriteria": [
        "GET /health returns 200 status code",
        "Response body contains {\"status\": \"healthy\"}",
        "Response time is under 100ms"
      ],
      "priority": 1,
      "complexity": "simple",
      "passes": false
    }
  ]
}
```

**Expected behavior:**
1. Test generation creates `tests/test_US_001.py` with 3 tests
2. Tests fail initially (no /health endpoint exists)
3. Implementation creates the endpoint
4. Tests pass
5. state.json updated
6. history.md appended
7. Git commit created

**If this works, the engine is ready for real work.**

---

## Guardrails

### What NOT to Build

❌ **No learnings.md**
- Knowledge goes in code (comments) or standards (docs)

❌ **No self-healing**
- If tests fail, BLOCK - don't try to fix

❌ **No integrations**
- No JIRA, Slack, webhooks
- Read from `prds/`, write to `state.json` and `history.md`

❌ **No cost optimization**
- Use Sonnet for everything in v1
- Don't add model selection logic

❌ **No progress estimation**
- Don't predict completion times
- Just execute work items

❌ **No UI**
- Command-line only
- Output to terminal is fine

---

## README.md Content

Create a README with:

```markdown
# Swanson Framework

**"Never half-ass two things. Whole-ass one thing."** - Ron Swanson

Cross-platform autonomous development framework. Works on macOS, Windows, and Linux.

Built on principles of quality craftsmanship, standards enforcement, and reliable overnight execution.

## Requirements
- Python 3.12+
- Claude Code CLI
- pytest
- git
- Windows 11+ (Windows) or macOS 13+ (macOS)

## Usage

### First-Time Setup (Required)

Run the interactive setup script:

```bash
python setup.py
```

This will:
1. Ask for your Anthropic API key
2. Create configuration files
3. Validate your setup

**OR** manually create one of these files:

#### Option 1: .env file (Recommended)
```bash
# Copy template
cp .env.template .env

# Edit .env and add your API key
# (Use notepad on Windows, nano/vim on macOS/Linux)
```

#### Option 2: config.json
```bash
# Copy template
cp config.example.json config.json

# Edit config.json and add your API key
# (Use notepad on Windows, nano/vim on macOS/Linux)
```

### Initialize Your Project

```bash
# From your project directory
python /path/to/swanson/init.py
```

This creates `.swanson/` directory with configuration templates.

### Run

```bash
# Cross-platform
python src/swanson/loop.py
```

### Check Status

```bash
# View current state
cat state.json        # macOS/Linux
type state.json       # Windows

# View history
tail -50 history.md   # macOS/Linux
Get-Content history.md -Tail 50  # Windows (PowerShell)

# View queue
ls prds/              # macOS/Linux
dir prds\             # Windows
```

### Verify Setup

```bash
python -c "from src.swanson.config import config; config.validate(); print('✓ Config valid')"
```

### Getting Your API Key

1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)
4. Paste it into `.env` or `config.json`

**Important:** Never commit your API key to git. Both `.env` and `config.json` are gitignored.

## Architecture

The Swanson Framework separates concerns:

**Framework Repo (swanson):**
- Core execution loop
- ATDD enforcement
- Standards loading
- Default templates

**Your Project:**
- `.swanson/` - Customized standards, vision
- `prds/` - Your work queue
- `src/` - Generated code
- `tests/` - Generated tests

See context-map.md for document structure and reading order.

## Philosophy

**Quality Over Speed:**
Swanson enforces standards and validates with real tests. Code must be right the first time.

**Autonomous Execution:**
Queue PRDs before bed, wake up to working software with passing tests.

**Brownfield Ready:**
Unlike tools that multiply chaos, Swanson transforms brownfield codebases through systematic tech debt cleanup.

## Platform Notes
- Uses Python for cross-platform compatibility
- Tested on macOS and Windows
- File paths use pathlib for platform independence
```

---

## Completion Checklist

Before considering the build complete:

- [ ] All files in File Structure exist
- [ ] loop.py contains ATDD flow logic (Python, not bash)
- [ ] All file paths use pathlib.Path for cross-platform compatibility
- [ ] context_loader.py loads right docs for each session type
- [ ] signal_detector.py parses Claude Code output
- [ ] executor.py invokes Claude Code with proper prompts
- [ ] state_manager.py reads/writes state.json correctly
- [ ] history_logger.py appends to history.md
- [ ] README.md has usage instructions for both Windows and macOS
- [ ] Test PRD executes successfully end-to-end on macOS
- [ ] Test PRD executes successfully end-to-end on Windows
- [ ] Tests are generated before implementation
- [ ] Tests must pass before story completes
- [ ] State persists between sessions
- [ ] History logs all completions
- [ ] No platform-specific code (no bash, no Unix tools)

**When all boxes are checked, Swanson is ready for production use on both platforms.**

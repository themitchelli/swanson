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

## How It Works

### ATDD Flow

```
Story → Test Generation → Verify Tests Fail → Implementation → Verify Tests Pass → Complete
```

### Test Generation Phase
1. Loads PRD and acceptance criteria
2. Generates pytest tests (one per AC minimum)
3. Verifies tests fail (expected state)
4. Blocks if tests pass (means they're stubbed)

### Implementation Phase
1. Loads tests and standards
2. Implements features to pass tests
3. Verifies all tests pass
4. Blocks if tests fail

### Completion Phase
1. Updates state.json
2. Appends to history.md
3. Creates git commit
4. Moves to next story

## Example PRD

Create `prds/001-FEAT-health-check.json`:

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
      "complexity": "simple"
    }
  ]
}
```

Then run:
```bash
python src/swanson/loop.py
```

Swanson will:
1. Generate tests for US-001
2. Verify tests fail
3. Implement the feature
4. Verify tests pass
5. Commit the code
6. Log to history

## Troubleshooting

### "API key not found"
- Make sure you created `.env` or `config.json`
- Verify your API key starts with `sk-ant-`
- Run `python setup.py` for interactive setup

### "BLOCKED: Test generation failed"
- Check that acceptance criteria are clear
- Verify PRD follows schema (see `.swanson/prd-schema.md`)
- Review Claude Code output for errors

### "Tests passing before implementation"
- Tests are stubbed (no real assertions)
- Feature already exists in codebase
- Review test file and fix assertions

### "Tests failing after implementation"
- Review pytest output
- Check standards compliance
- Verify all acceptance criteria addressed

## Contributing

Swanson follows its own philosophy: never half-ass two things. If you want to contribute, whole-ass one thing at a time.

## License

MIT

## Credits

Named after Ron Swanson, Director of the Pawnee Parks and Recreation Department, who believed in quality craftsmanship and doing things right the first time.

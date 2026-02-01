# Engineering Standards

## Purpose
This document defines quality expectations for all code produced by the engine. These standards apply to every story, every commit, every test.

---

## Code Quality

### Function Length
- Maximum 50 lines per function
- If a function exceeds 50 lines, extract helper functions
- Exception: Test functions can be longer if testing multiple scenarios

### Complexity
- Maximum cyclomatic complexity: 10
- If complexity exceeds 10, refactor into smaller functions
- Use early returns to reduce nesting

### Naming Conventions
- Functions: `snake_case` (Python), `camelCase` (JavaScript)
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`
- Names must be descriptive: `get_user_by_id`, not `get_usr`

### Comments
- Document WHY, not WHAT
- Good: `# Hash password to prevent plaintext storage`
- Bad: `# Call bcrypt.hash()`
- Complex algorithms need explanation
- Non-obvious decisions need justification

### Error Handling
- Never swallow exceptions silently
- Always log errors with context
- Return meaningful error messages to users
- Use specific exception types, not generic `Exception`

```python
# Good
try:
    user = get_user(user_id)
except UserNotFoundError as e:
    logger.error(f"User {user_id} not found: {e}")
    return {"error": "User not found"}, 404

# Bad
try:
    user = get_user(user_id)
except:
    pass
```

---

## Testing Standards

### Test Coverage
- Every acceptance criterion = at least one test
- Tests must be in `tests/` directory
- Test file naming: `test_<module>.py`
- Test function naming: `test_<behavior>_<expected_outcome>`

### Test Structure (AAA Pattern)
```python
def test_user_login_with_valid_credentials():
    # Arrange
    user = create_test_user(email="test@example.com", password="secret")
    
    # Act
    response = client.post("/api/login", json={
        "email": "test@example.com",
        "password": "secret"
    })
    
    # Assert
    assert response.status_code == 200
    assert "token" in response.json()
```

### Test Independence
- Each test must run independently
- Use fixtures for setup/teardown
- No shared state between tests
- Tests must pass in any order

### Test Data
- Use factories or fixtures for test data
- Never hardcode production data in tests
- Clean up test data after each test

### Non-Functional Requirements Testing
Performance:
```python
def test_api_response_time():
    start = time.time()
    response = client.get("/api/users")
    duration = time.time() - start
    assert duration < 0.2, f"Response took {duration}s, expected < 0.2s"
```

Security:
```python
def test_password_is_hashed():
    user = create_user(password="plaintext")
    assert user.password != "plaintext"
    assert user.password.startswith("$2b$")  # bcrypt prefix
```

Error Handling:
```python
def test_missing_email_returns_400():
    response = client.post("/api/login", json={"password": "secret"})
    assert response.status_code == 400
    assert "email" in response.json()["error"].lower()
```

---

## API Standards

### REST Conventions
- Use standard HTTP methods: GET, POST, PUT, DELETE, PATCH
- Resource naming: plural nouns (`/users`, not `/user`)
- ID in path for single resources: `/users/123`
- Query params for filtering: `/users?status=active`

### Status Codes
| Code | Usage |
|------|-------|
| 200 | Successful GET, PUT, PATCH |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE (no content) |
| 400 | Bad request (client error) |
| 401 | Unauthorized (missing/invalid auth) |
| 403 | Forbidden (authenticated but not allowed) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 500 | Server error |

### Response Format
```json
// Success
{
  "data": { ... },
  "meta": { "timestamp": "2026-02-01T20:00:00Z" }
}

// Error
{
  "error": "User not found",
  "code": "USER_NOT_FOUND",
  "meta": { "timestamp": "2026-02-01T20:00:00Z" }
}
```

### Request Validation
- Validate all inputs
- Return 400 with specific error message for invalid data
- Never trust client input
- Sanitize before processing

---

## Security Standards

### Authentication
- Never store passwords in plaintext
- Use bcrypt for password hashing (minimum cost factor: 12)
- Use JWT for session tokens
- Token expiration: maximum 1 hour for APIs, 24 hours for web apps

### Authorization
- Verify user permissions before allowing actions
- Return 403 (not 404) for unauthorized access to existing resources
- Never expose sensitive data in error messages

### Input Validation
- Validate all user input
- Use allowlists, not denylists
- Escape output to prevent XSS
- Use parameterized queries to prevent SQL injection

### Secrets Management
- Never commit secrets to git
- Use environment variables for API keys, passwords, tokens
- Rotate secrets regularly
- Log secret access (but not the secrets themselves)

### Logging Security
```python
# Good - log the attempt, not the password
logger.warning(f"Failed login attempt for {email}")

# Bad - logs sensitive data
logger.warning(f"Failed login: {email}/{password}")
```

---

## Git Standards

### Commit Messages
Format: `<type>: <description> (<story-id>)`

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `chore:` - Maintenance (dependencies, config)
- `refactor:` - Code restructure without behavior change
- `test:` - Adding or updating tests

Examples:
```
feat: add user login endpoint (US-002)
fix: handle missing email in registration (US-001)
docs: update API documentation (US-003)
chore: upgrade pytest to 8.0 (US-004)
```

### Commit Scope
- One commit per story completion
- Include all related changes (code + tests + docs)
- Never commit broken code
- Never commit commented-out code

### Branch Strategy (If Used)
- `main` branch is always deployable
- Feature branches: `feature/US-XXX-description`
- Merge to main only after tests pass

---

## File Organization

### Python Projects
```
/
├── src/
│   └── <package>/
│       ├── __init__.py
│       ├── models.py
│       ├── routes.py
│       ├── services.py
│       └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_routes.py
│   └── test_services.py
├── requirements.txt
└── README.md
```

### JavaScript/Node Projects
```
/
├── src/
│   ├── routes/
│   ├── controllers/
│   ├── services/
│   └── utils/
├── tests/
├── package.json
└── README.md
```

### General Rules
- Group by feature, not by type (when projects grow)
- Keep related files together
- Max 10 files per directory (create subdirectories if exceeded)

---

## Documentation Standards

### README Requirements
Every project must have a README with:
- Project description (what it does)
- Installation instructions
- Usage examples
- API documentation (if applicable)
- Testing instructions
- License

### Code Documentation
- Public APIs must have docstrings
- Include parameter types and return types
- Document exceptions that can be raised

```python
def get_user_by_id(user_id: int) -> User:
    """
    Retrieve a user by their ID.
    
    Args:
        user_id: The unique identifier for the user
        
    Returns:
        User object if found
        
    Raises:
        UserNotFoundError: If user with given ID doesn't exist
    """
    ...
```

### API Documentation
- Document all endpoints
- Include request/response examples
- Document error cases
- Keep docs in sync with code

---

## Dependency Management

### Adding Dependencies
- Only add dependencies that are actually needed
- Prefer standard library over third-party when possible
- Check license compatibility
- Pin versions (not `latest` or `*`)

### Updating Dependencies
- Regular security updates
- Test after updating
- Update lockfiles (requirements.txt, package-lock.json)

### Python
```
# requirements.txt - pin versions
flask==3.0.0
pytest==8.0.0
bcrypt==4.1.2
```

### JavaScript
```json
// package.json - pin versions
{
  "dependencies": {
    "express": "4.18.2",
    "jsonwebtoken": "9.0.2"
  }
}
```

---

## Performance Standards

### Response Times
- API endpoints: < 200ms for simple queries
- Database queries: < 100ms for indexed lookups
- Page load: < 2 seconds

### Resource Usage
- Memory: Monitor for leaks, clean up resources
- Database connections: Use connection pooling
- File handles: Close after use

### Optimization
- Don't optimize prematurely
- Measure before optimizing
- Use caching where appropriate
- Index database columns used in WHERE clauses

---

## Error Messages

### User-Facing Errors
- Clear and actionable
- Don't expose internal details
- Include what went wrong and how to fix it

```python
# Good
"Email address is required"
"Password must be at least 8 characters"

# Bad
"Validation error in field 'email'"
"Error: NoneType object has no attribute 'password'"
```

### Logs
- Include context (user ID, request ID, timestamp)
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Don't log sensitive data

```python
# Good
logger.error(f"Failed to process payment for user {user_id}", 
             exc_info=True)

# Bad
logger.error("Error occurred")
```

---

## Configuration Management

### API Key Storage (CRITICAL)

**Problem:** Anthropic API keys are required but fragile - environment variables get lost, shells handle them differently.

**Solution:** Multi-layer configuration with file-based persistence.

#### Layer 1: .env File (Recommended)
```bash
# .env file (gitignored)
ANTHROPIC_API_KEY=sk-ant-actual-key-here
FADE_MODEL=sonnet
```

Load with python-dotenv:
```python
from pathlib import Path
from dotenv import load_dotenv
import os

env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)
api_key = os.getenv("ANTHROPIC_API_KEY")
```

#### Layer 2: config.json (Alternative)
```json
{
  "anthropic_api_key": "sk-ant-actual-key-here",
  "model": "sonnet",
  "log_level": "INFO"
}
```

#### Layer 3: Environment Variables (Override)
```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-key-here"

# macOS/Linux
export ANTHROPIC_API_KEY="sk-ant-key-here"
```

#### Priority Order
1. Environment variables (highest)
2. config.json
3. .env file
4. Defaults (lowest)

#### Security Rules
- ✅ Commit: `.env.template`, `config.example.json` (templates)
- ❌ Never commit: `.env`, `config.json` (actual keys)
- ✅ Add to .gitignore: `.env`, `config.json`
- ✅ Validate on startup: Fail fast if key missing/invalid

#### Error Handling
```python
if not api_key:
    raise RuntimeError(
        "ANTHROPIC_API_KEY not found. Create .env file or set environment variable.\n"
        "See .env.template for example."
    )

if not api_key.startswith("sk-ant-"):
    raise RuntimeError(f"Invalid API key format: {api_key[:10]}...")
```

---

## Cross-Platform Compatibility

### File Paths
Always use `pathlib.Path` for file operations:

```python
# Good - works on Windows and Unix
from pathlib import Path

test_file = Path("tests") / f"test_{story_id}.py"
prd_path = Path("prds") / "001-FEAT-user-auth.json"

# Bad - Unix-only
test_file = f"tests/test_{story_id}.py"
prd_path = "prds/001-FEAT-user-auth.json"
```

### Shell Commands
Use `subprocess.run()` with list arguments (not strings):

```python
# Good - cross-platform
import subprocess

result = subprocess.run(
    ["pytest", "tests/test_US_001.py"],
    capture_output=True,
    text=True
)

# Bad - platform-specific
result = os.system("pytest tests/test_US_001.py")
```

### Line Endings
- Git handles line ending conversion
- Don't hardcode `\n` or `\r\n`
- Use `Path.read_text()` and `Path.write_text()` which handle line endings

### Platform Detection
Only when absolutely necessary:

```python
import sys
import platform

if platform.system() == "Windows":
    # Windows-specific code
elif platform.system() == "Darwin":
    # macOS-specific code
else:
    # Linux-specific code
```

### Avoid Platform-Specific Tools
❌ Don't use:
- bash/sh scripts
- Unix tools: awk, sed, grep, tail
- Windows batch files
- PowerShell scripts (for core logic)

✅ Do use:
- Python for all scripting
- subprocess for external tools (git, pytest, claude-code)
- pathlib for file paths
- Standard library for file operations

### Environment Variables
```python
# Good - cross-platform
import os
api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# Set in shell:
# Windows: $env:ANTHROPIC_API_KEY = "key"
# Unix: export ANTHROPIC_API_KEY="key"
```

---

## When Standards Conflict

If a story's acceptance criteria conflict with these standards:
1. Block and report the conflict
2. Do NOT silently ignore standards
3. Do NOT silently ignore acceptance criteria
4. Request clarification from human

Example conflict:
- AC: "Store password in plaintext"
- Standard: "Never store passwords in plaintext"
- **Action:** Block with message explaining the security violation

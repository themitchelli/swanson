# Coding Standards Template

<!-- Purpose: Define quality expectations and coding standards for your project -->

## Purpose
This template provides example coding standards that ensure consistent, maintainable, high-quality code across your project.

---

## Code Quality Standards

### Function Length
- Functions should be under 50 lines
- If longer, break into smaller functions
- Each function should do one thing well

### Cyclomatic Complexity
- Maximum complexity: 10 per function
- Use early returns to reduce nesting
- Extract complex conditions into named functions

### Naming Conventions
- **Functions**: `snake_case` (Python) or `camelCase` (JavaScript)
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (Python) or use `#` (JavaScript)
- **Names should be descriptive**: `get_user_by_id()` not `get()`

### Comments and Documentation
- Docstrings for all public functions/classes
- Inline comments for complex logic only
- Don't comment obvious code
- Update comments when code changes

---

## Testing Standards

### Coverage
- Minimum 80% code coverage
- 100% coverage for critical paths
- Test both happy path and error cases

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data
    user = create_test_user()

    # Act - Execute the behavior
    result = authenticate_user(user.email, user.password)

    # Assert - Verify the outcome
    assert result.is_authenticated
    assert result.token is not None
```

### Test Independence
- Tests must not depend on each other
- Tests can run in any order
- Each test cleans up after itself
- Use fixtures for shared setup

### Test Naming
- Use descriptive names: `test_login_with_invalid_password_returns_401`
- Include the scenario being tested
- Include the expected outcome

### Non-Functional Requirements (NFR) Tests
Always include tests for:
- **Performance**: Response times, throughput
- **Security**: Input validation, auth checks
- **Error Handling**: Edge cases, invalid inputs
- **Usability**: API contracts, error messages

---

## API Standards (if applicable)

### REST Conventions
- Use standard HTTP methods: GET, POST, PUT, PATCH, DELETE
- Use plural nouns: `/api/users` not `/api/user`
- Use status codes correctly:
  - 200 OK - Success with response body
  - 201 Created - Resource created
  - 400 Bad Request - Invalid input
  - 401 Unauthorized - Authentication required
  - 403 Forbidden - Insufficient permissions
  - 404 Not Found - Resource doesn't exist
  - 500 Internal Server Error - Server error

### Response Format
```json
{
  "data": { ... },
  "error": null,
  "timestamp": "2026-02-01T20:00:00Z"
}
```

---

## Security Standards

### Input Validation
- Validate all user input at system boundaries
- Use allowlists, not denylists
- Sanitize input before use in queries or commands
- Reject invalid input with clear error messages

### Authentication & Authorization
- Never store passwords in plaintext
- Use bcrypt or similar for password hashing
- Validate JWTs on every protected endpoint
- Check permissions before allowing actions

### Secrets Management
- Never commit secrets to git
- Use environment variables or secret managers
- Rotate credentials regularly
- Use different credentials for dev/prod

### OWASP Top 10
Be aware of and prevent:
- SQL Injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Insecure Direct Object References
- Security Misconfiguration

---

## Git Standards

### Commit Messages
Follow conventional commits format:
```
<type>: <description> (<story-id>)

Examples:
feat: implement user login (US-002)
fix: handle missing email in registration (BUG-001)
refactor: extract validation logic (US-003)
test: add edge cases for auth (US-002)
docs: update API documentation (US-004)
```

### Commit Scope
- One logical change per commit
- All tests pass before committing
- Commit messages explain "why" not "what"

### Branch Strategy (if applicable)
- `main` - production-ready code
- `feature/story-id` - feature branches
- Merge only when tests pass

---

## Error Handling

### Python
```python
def risky_operation():
    """Do something that might fail."""
    try:
        result = do_something()
        return result
    except SpecificError as e:
        logger.error(f"Operation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise RuntimeError("Operation failed") from e
```

### Error Messages
- Be specific: "Email is required" not "Invalid input"
- Include context: "User not found: user@example.com"
- Don't expose sensitive data in errors
- Log detailed errors, return safe errors to users

---

## Performance Standards

### Response Times (if applicable)
- API endpoints: < 200ms (95th percentile)
- Database queries: < 50ms
- File operations: < 100ms

### Resource Usage
- Avoid N+1 queries
- Use pagination for large datasets
- Close resources (files, connections) explicitly
- Profile before optimizing

---

## Documentation Standards

### README.md
Every project should have:
- What the project does
- Installation instructions
- Usage examples
- Configuration options
- Troubleshooting guide

### Code Documentation
- Public APIs must be documented
- Include parameter types and return types
- Provide usage examples for complex functions
- Document side effects and exceptions

---

## Python-Specific Standards

### Type Hints
```python
from typing import List, Optional, Dict

def get_users(active_only: bool = True) -> List[Dict[str, str]]:
    """Get list of users."""
    pass
```

### Imports
- Standard library first
- Third-party packages second
- Local imports third
- One import per line
- Sort alphabetically within groups

### File Structure
```
project/
├── src/
│   └── package/
│       ├── __init__.py
│       ├── module1.py
│       └── module2.py
├── tests/
│   ├── test_module1.py
│   └── test_module2.py
├── requirements.txt
└── README.md
```

---

## Instructions for Use

1. Copy this template to `.swanson/standards.md` in your project
2. Customize sections to match your tech stack and requirements
3. Add project-specific standards as needed
4. Reference it during all implementation sessions
5. Enforce standards through code review and automated linting

Remember: Standards exist to ensure quality and consistency, not to slow you down. Good standards make development faster in the long run.

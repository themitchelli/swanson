# PRD Schema

## Purpose
Defines the structure for Product Requirement Documents (PRDs) that the engine processes.

## File Format
- **Format:** JSON
- **Encoding:** UTF-8
- **Naming:** `{NUMBER}-{TYPE}-{slug}.json` (e.g., `001-FEAT-user-auth.json`)

## Required Fields

```json
{
  "type": "feature|bug|enhancement|spike|chore",
  "name": "Human-readable name",
  "description": "What this PRD accomplishes and why",
  "userStories": [
    {
      "id": "US-001",
      "title": "Story title",
      "description": "What this story does",
      "acceptanceCriteria": [
        "Specific, testable criterion",
        "Another testable criterion"
      ],
      "priority": 1,
      "complexity": "simple|medium|complex",
      "passes": false
    }
  ]
}
```

## Field Definitions

### PRD Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | One of: `feature`, `bug`, `enhancement`, `spike`, `chore`, `tech-debt` |
| `name` | string | Yes | Short, descriptive name |
| `description` | string | Yes | What this PRD accomplishes and why it matters |
| `userStories` | array | Yes | At least one user story |

**Note on `tech-debt` type:**
Reserved for future brownfield rescue mode (systematic cleanup of legacy code, security fixes, refactoring). Not required for v1 but included in schema to avoid breaking changes later.

**Type Descriptions:**
- `feature` - New functionality
- `bug` - Fix broken behavior
- `enhancement` - Improve existing functionality
- `spike` - Research/exploration
- `chore` - Maintenance, dependencies, operational work
- `tech-debt` - Refactoring, security fixes, code quality improvements (future use)

### User Story Level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Format: `US-XXX` (e.g., `US-001`, `US-002`) |
| `title` | string | Yes | Short, descriptive title |
| `description` | string | Yes | What this story accomplishes |
| `acceptanceCriteria` | array | Yes | List of testable criteria (minimum 1) |
| `priority` | number | Yes | Execution order within PRD (1 = first) |
| `complexity` | string | No | One of: `simple`, `medium`, `complex` (defaults to `medium`) |
| `passes` | boolean | Yes | Always `false` initially, set to `true` when tests pass |

## Acceptance Criteria Rules

Each criterion MUST be:
1. **Testable:** Can be verified by a pytest test
2. **Specific:** No ambiguity about what "done" means
3. **Observable:** Can be verified by running code or checking output

### Functional Criteria Examples
✅ Good:
- "User can login with email and password"
- "Invalid password returns 401 status code"
- "Session token is created on successful login"

❌ Bad:
- "Login works" (too vague)
- "User is happy" (not testable)
- "Code is clean" (subjective)

### Non-Functional Requirements (NFRs)

Include NFRs as acceptance criteria:

✅ Performance:
- "API responds in under 200ms"
- "Query completes in under 1 second for 10K records"

✅ Security:
- "Password is hashed with bcrypt"
- "JWT token expires after 1 hour"

✅ Logging:
- "Failed login attempts are logged"
- "Logs are JSON formatted"

✅ Error Handling:
- "Missing email returns 400 with error message"
- "Database errors return 500 status"

## Complexity Guidelines

| Complexity | Indicators | Estimated Effort |
|-----------|-----------|------------------|
| `simple` | < 5 AC, typo fix, docs update, config change | < 4 hours |
| `medium` | 5-15 AC, standard feature, single module | 4 hours - 1 day |
| `complex` | > 15 AC, architecture change, multi-system integration | > 1 day |

## Complete Example

```json
{
  "type": "feature",
  "name": "User Authentication",
  "description": "Implement JWT-based authentication for API access. Users can register, login, and maintain sessions.",
  "userStories": [
    {
      "id": "US-001",
      "title": "User Registration",
      "description": "New users can create accounts with email and password",
      "acceptanceCriteria": [
        "POST /api/register accepts email and password",
        "Email must be unique (returns 409 if exists)",
        "Password is hashed with bcrypt before storage",
        "Returns 201 with user ID on success",
        "Returns 400 if email or password missing"
      ],
      "priority": 1,
      "complexity": "medium",
      "passes": false
    },
    {
      "id": "US-002",
      "title": "User Login",
      "description": "Existing users can authenticate and receive session token",
      "acceptanceCriteria": [
        "POST /api/login accepts email and password",
        "Returns 200 with JWT token on valid credentials",
        "Returns 401 on invalid password",
        "Returns 404 if user doesn't exist",
        "JWT token expires after 1 hour",
        "Failed login attempts are logged"
      ],
      "priority": 2,
      "complexity": "medium",
      "passes": false
    },
    {
      "id": "US-003",
      "title": "Protected Endpoints",
      "description": "API endpoints require valid JWT token",
      "acceptanceCriteria": [
        "Requests without token return 401",
        "Requests with invalid token return 401",
        "Requests with expired token return 401",
        "Requests with valid token proceed normally",
        "Token validation completes in under 50ms"
      ],
      "priority": 3,
      "complexity": "simple",
      "passes": false
    }
  ]
}
```

## Validation Rules

The engine MUST reject PRDs that:
- Are missing required fields
- Have empty `userStories` array
- Have stories with < 1 acceptance criterion
- Have invalid `type` values
- Have malformed story IDs (not `US-XXX` format)
- Have non-boolean `passes` values

## State Updates

The engine updates `passes` field when:
- All tests for a story pass
- State transitions from `false` → `true`
- NEVER transitions from `true` → `false` (tests can't "un-pass")

When all stories have `passes: true`, PRD moves to archive.

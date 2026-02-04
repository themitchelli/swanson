# PRD Schema Documentation

<!-- Purpose: Define the exact JSON schema for Product Requirement Documents -->

## Purpose
This document defines the exact schema for PRD JSON files. All PRDs must follow this schema to be processed by the framework.

---

## Complete PRD Schema

### Required Structure
A PRD is a JSON file with a `userStories` wrapper containing an array of user story objects.

```json
{
  "userStories": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "acceptanceCriteria": ["string"],
      "priority": number,
      "complexity": "simple|moderate|complex"
    }
  ]
}
```

---

## Field Specifications

### Root Level
- **userStories** (required): Array of user story objects
  - Must contain at least 1 story
  - Each story must follow the user story schema below

### User Story Object

#### id (required)
- Type: `string`
- Format: `PREFIX-NNN` where:
  - PREFIX: `US` (user story), `BUG` (bug fix), `TECH` (technical debt)
  - NNN: 3-digit number, zero-padded
- Examples: `US-001`, `BUG-042`, `TECH-003`
- Must be unique within the PRD

#### title (required)
- Type: `string`
- Length: 5-100 characters
- Should be concise and descriptive
- Example: "User login with email and password"

#### description (required)
- Type: `string`
- Length: 20-500 characters
- Provides context and details about the story
- Example: "Implement a login endpoint that accepts email and password, validates credentials, and returns a JWT token."

#### acceptanceCriteria (required)
- Type: `array` of `string`
- Must contain at least 1 criterion
- Each criterion should be:
  - Testable (can be verified with a test)
  - Specific (no ambiguity)
  - Complete (includes expected behavior)
- Format: Start with action verb when possible
- Examples:
  - "POST /api/login accepts email and password"
  - "Returns 200 with JWT token on valid credentials"
  - "Returns 401 on invalid password"

#### priority (optional)
- Type: `number`
- Range: 1-5 (1 = highest priority)
- Default: 3
- Used for ordering stories within a PRD

#### complexity (optional)
- Type: `string`
- Values: `"simple"`, `"moderate"`, `"complex"`
- Default: `"moderate"`
- Guidelines:
  - **simple**: 1-3 ACs, < 2 hours work
  - **moderate**: 4-7 ACs, 2-8 hours work
  - **complex**: 8+ ACs, > 8 hours work (consider splitting)

---

## Complete Example PRD

```json
{
  "userStories": [
    {
      "id": "US-001",
      "title": "User Registration",
      "description": "Allow new users to create an account with email and password. Validate email format and password strength.",
      "acceptanceCriteria": [
        "POST /api/register accepts email and password",
        "Email must be valid format (contains @ and domain)",
        "Password must be at least 8 characters",
        "Password must contain at least one number",
        "Returns 201 with user ID on successful registration",
        "Returns 400 if email already exists",
        "Returns 400 if email or password is invalid",
        "Passwords are hashed with bcrypt before storage"
      ],
      "priority": 1,
      "complexity": "moderate"
    },
    {
      "id": "US-002",
      "title": "User Login",
      "description": "Allow existing users to log in with email and password. Return a JWT token for authenticated sessions.",
      "acceptanceCriteria": [
        "POST /api/login accepts email and password",
        "Returns 200 with JWT token on valid credentials",
        "Returns 401 on invalid password",
        "Returns 404 if user doesn't exist",
        "JWT token expires after 1 hour",
        "JWT token contains user ID in payload"
      ],
      "priority": 1,
      "complexity": "moderate"
    },
    {
      "id": "BUG-001",
      "title": "Fix password reset email",
      "description": "Password reset emails are not being sent due to SMTP configuration error.",
      "acceptanceCriteria": [
        "POST /api/password-reset sends email to valid user",
        "Email contains password reset link",
        "Link expires after 1 hour",
        "Returns 404 if user email doesn't exist",
        "Returns 429 if too many requests (rate limiting)"
      ],
      "priority": 2,
      "complexity": "simple"
    }
  ]
}
```

---

## Validation Rules

### File Naming
PRD files should follow this naming convention:
```
PRD-NNN-short-description.json

Examples:
PRD-001-user-auth.json
PRD-002-payment-integration.json
PRD-003-add-missing-templates.json
```

### Schema Validation
Before processing, validate that:
1. JSON is valid (can be parsed)
2. Root object contains `userStories` key
3. `userStories` is an array with at least 1 story
4. Each story has all required fields
5. All story IDs are unique
6. All acceptance criteria are non-empty strings

### Content Validation
Also check that:
1. Acceptance criteria are testable (can write pytest tests)
2. Story descriptions provide enough context
3. No story has conflicting or contradictory ACs
4. Complex stories (8+ ACs) are flagged for potential splitting

---

## Acceptance Criteria Best Practices

### Good Acceptance Criteria
✅ "GET /api/users returns 200 with array of user objects"
✅ "Response time is under 100ms for 95th percentile"
✅ "Passwords are hashed with bcrypt before storage"
✅ "Returns 401 if JWT token is missing or invalid"

### Bad Acceptance Criteria
❌ "Login works" (not specific)
❌ "Handle errors" (not testable)
❌ "Should be fast" (not measurable)
❌ "User is happy" (not verifiable)

### Tips
1. Start with action verbs: "Returns", "Validates", "Sends", "Creates"
2. Include expected behavior: "Returns 200" not just "Returns success"
3. Specify error cases: "Returns 404 if user not found"
4. Include non-functional requirements: response times, security requirements
5. One behavior per criterion (easier to test)

---

## Using This Schema

### For Test Generation
When generating tests:
1. Read the PRD JSON file
2. Parse the `userStories` array
3. Find the story with matching `id`
4. Create one test per `acceptanceCriteria` item (minimum)
5. Add additional NFR tests as needed
6. Save to `tests/test_<story_id>.py`

### For Implementation
When implementing features:
1. Read the PRD JSON file
2. Parse the `userStories` array
3. Find the story with matching `id`
4. Read the generated tests
5. Implement features to make tests pass
6. Verify all acceptance criteria are met

### For Validation
When validating a PRD:
1. Check JSON syntax
2. Validate schema structure
3. Verify all required fields present
4. Check uniqueness of story IDs
5. Verify acceptance criteria are testable

---

## Common Patterns

### Feature Story
```json
{
  "id": "US-XXX",
  "title": "Feature name",
  "description": "What and why",
  "acceptanceCriteria": [
    "Happy path behavior",
    "Error case 1",
    "Error case 2",
    "Performance requirement",
    "Security requirement"
  ]
}
```

### Bug Fix
```json
{
  "id": "BUG-XXX",
  "title": "Fix [problem]",
  "description": "Current behavior and expected behavior",
  "acceptanceCriteria": [
    "Fixed behavior works correctly",
    "Regression test added",
    "No side effects on related features"
  ]
}
```

### Technical Debt
```json
{
  "id": "TECH-XXX",
  "title": "Refactor [component]",
  "description": "Why refactoring is needed",
  "acceptanceCriteria": [
    "Code follows standards",
    "Test coverage maintained or improved",
    "Performance not degraded",
    "All existing tests still pass"
  ]
}
```

---

## Instructions for Use

1. Copy this template to `.swanson/prd-schema.md` in your project
2. Reference it when creating PRD JSON files
3. Use it to validate PRDs before queuing them
4. Include it in context during test generation sessions

Remember: Well-structured PRDs with clear acceptance criteria make test generation and implementation much more reliable.

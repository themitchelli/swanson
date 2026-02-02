# Product Vision Template

<!-- Purpose: Define the strategic direction and boundaries for your project -->

## Purpose
This template helps you define what your project does and doesn't do. A clear vision prevents scope creep and keeps development focused.

## Example Product Vision

### What We're Building
[Describe your product in 2-3 sentences. What problem does it solve? Who is it for?]

Example:
"We're building an autonomous development framework that enforces ATDD practices. It enables developers to queue work overnight and wake up to working, tested software. The framework is designed for quality-conscious teams who value standards over speed."

### Core Principles
[List 3-5 fundamental principles that guide all decisions]

Example:
1. **External Validation** - Tests validate behavior, not internal assumptions
2. **Simplicity** - Simple components, clear contracts, minimal abstractions
3. **Strict Contracts** - Tests are the contract, PRDs define requirements
4. **Quality Over Speed** - Code must be right the first time
5. **Autonomous Operation** - Should run unattended for hours

### What This Project IS
[List what's explicitly in scope]

Example:
- A test-driven development loop
- A standards enforcement system
- A work queue processor
- A cross-platform Python tool

### What This Project IS NOT
[List what's explicitly out of scope - this is critical]

Example:
- Not a code generation tool
- Not an AI assistant for writing code manually
- Not a cost optimization system
- Not a project management platform
- Not a CI/CD replacement

### Success Criteria for v1
[Define what "done" looks like for version 1]

Example:
- Can execute one PRD with 3 stories end-to-end
- Tests are generated before implementation
- Tests must pass before story marked complete
- State persists between sessions
- Works on both macOS and Windows

### Future Vision (v2+)
[Optional: What comes after v1? Keep this aspirational]

Example:
- Brownfield codebase rescue mode
- Cost optimization with model selection
- Multi-repo coordination
- Enterprise scale operation

### Boundaries and Constraints
[Technical or business constraints]

Example:
- Must work on Windows and macOS
- Must use Python 3.12+
- Must integrate with Claude Code CLI
- API costs should be predictable
- No external dependencies beyond Python standard library

---

## Instructions for Use

1. Copy this template to `.swanson/product-vision.md` in your project
2. Fill in each section with your project's specific vision
3. Keep it updated as your vision evolves
4. Reference it when deciding whether to add new features (default: no)
5. Share it with Claude Code at the start of implementation sessions

Remember: A clear "no" is more valuable than an unclear "maybe."

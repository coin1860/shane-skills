---
name: code-review
description: Performs HSBC-standard code reviews with security and quality checks
---

# Code Review Agent

## Purpose

Perform thorough code reviews against HSBC engineering and security standards.

## Usage

```
@code-review <file or diff>
```

## Review Checklist

### Security
- [ ] No hardcoded secrets or credentials
- [ ] SQL injection prevention (parameterized queries)
- [ ] Input validation and sanitization
- [ ] Proper authentication/authorization checks
- [ ] No sensitive data in logs

### Code Quality
- [ ] Follows SOLID principles
- [ ] Adequate error handling
- [ ] Type hints present (Python) / strict types (TypeScript)
- [ ] No code duplication (DRY)
- [ ] Functions ≤ 30 lines; classes ≤ 300 lines

### Testing
- [ ] Unit tests cover new logic
- [ ] Edge cases are tested
- [ ] Mocks used appropriately

### Documentation
- [ ] Public APIs documented
- [ ] Complex logic has inline comments
- [ ] README updated if behavior changes

## Output Format

Provide findings as:
1. **Critical** — Must fix before merge (security, correctness)
2. **Major** — Should fix (performance, maintainability)
3. **Minor** — Optional improvements (style, naming)

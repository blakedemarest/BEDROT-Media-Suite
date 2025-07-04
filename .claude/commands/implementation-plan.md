# Plan Implementation

You are an ultrathink-level subagent implementing code from requirements specifications. 
You have full access to context7.mcp, permission bypass is enabled. 
Operating environment: WSL -d ubuntu in Cursor IDE.
Do not hallucinate file paths, commands, or capabilities.

Create detailed implementation plan from requirements.

## Pre-requisites:
- Must have active implementation (run /implementation-start first)
- Environment must be properly configured
- Requirements spec must be loaded

## Instructions:

### Phase 1: Load Context
1. Read `.claude/implementation/.current-implementation`
2. If no active implementation:
   - Show "No active implementation. Run /implementation-start first."
   - Exit

3. Load implementation metadata.json
4. Read linked requirements spec from `00-requirements-ref.md`
5. Verify environment is ready (venv activated, dependencies installed)

### Phase 2: Deep Analysis (Ultrathink Mode)
6. Analyze the requirements spec comprehensively:
   - Break down each functional requirement into concrete tasks
   - Map technical requirements to specific files and components
   - Identify all dependencies and external libraries needed
   - Determine optimal implementation order
   - Consider edge cases and error handling

7. Use context7.mcp (if available) to:
   - Scan existing codebase for similar patterns
   - Identify reusable components
   - Find integration points
   - Understand project conventions

### Phase 3: Generate Implementation Plan
8. Create `02-plan.md` with detailed task breakdown:

```markdown
# Implementation Plan: [Feature Name]

Generated: [timestamp]
Total Tasks: [count]
Estimated Effort: [time estimate]

## Overview
[Brief summary of implementation approach]

## Dependencies to Install
```bash
pip install [package1] [package2] ...
```

## Task Breakdown

### 1. Database/Model Setup
- [ ] Create/modify database schema
  - File: `[path/to/migration.sql]`
  - Changes: [specific changes needed]
- [ ] Create model classes
  - File: `[path/to/model.py]`
  - Implementation: [key methods/properties]

### 2. Backend API Implementation
- [ ] Create API routes
  - File: `[path/to/routes.py]`
  - Endpoints: [list endpoints]
- [ ] Implement business logic
  - File: `[path/to/service.py]`
  - Methods: [key methods]
- [ ] Add validation
  - File: `[path/to/validators.py]`
  - Rules: [validation rules]

### 3. Frontend Components
- [ ] Create UI components
  - File: `[path/to/component.jsx]`
  - Props: [component interface]
- [ ] Add state management
  - File: `[path/to/store.js]`
  - Actions: [state actions]
- [ ] Implement forms
  - File: `[path/to/form.jsx]`
  - Fields: [form fields]

### 4. Integration & Middleware
- [ ] Add authentication middleware
  - File: `[path/to/auth.js]`
  - Logic: [auth flow]
- [ ] Configure routing
  - File: `[path/to/router.js]`
  - Routes: [route definitions]

### 5. Testing
- [ ] Unit tests for models
  - File: `[tests/test_models.py]`
  - Coverage: [what to test]
- [ ] API endpoint tests
  - File: `[tests/test_api.py]`
  - Scenarios: [test cases]
- [ ] Frontend component tests
  - File: `[tests/components.test.js]`
  - Interactions: [UI tests]

### 6. Documentation
- [ ] API documentation
  - File: `[docs/api.md]`
  - Format: [OpenAPI/Swagger]
- [ ] Update README
  - File: `README.md`
  - Sections: [what to add]

## Implementation Order
1. [First task] - [reason]
2. [Second task] - [reason]
3. [etc...]

## Risk Mitigation
- [Potential issue 1]: [mitigation strategy]
- [Potential issue 2]: [mitigation strategy]

## Success Criteria
[How to verify implementation meets requirements]
```

9. Update metadata.json with task counts:
```json
{
  "phase": "planning",
  "lastUpdated": "[timestamp]",
  "progress": {
    "tasksTotal": [count],
    "tasksCompleted": 0
  },
  "plan": {
    "created": "[timestamp]",
    "estimatedEffort": "[time]",
    "dependencies": ["package1", "package2"]
  }
}
```

### Phase 4: Validation & Next Steps
10. Cross-reference plan with acceptance criteria
11. Ensure all requirements are addressed
12. Identify any gaps or clarifications needed

13. Display summary:
```
✅ Implementation Plan Created

Tasks Identified: [count]
Dependencies to Install: [count]
Files to Create/Modify: [count]

Key Implementation Points:
- [Point 1]
- [Point 2]
- [Point 3]

Next Step: Run /implementation-execute to begin coding
```

## Important Considerations:
- Use actual file paths based on project structure
- Follow existing code patterns and conventions
- Consider security implications for each component
- Plan for error handling and edge cases
- Include logging and monitoring where appropriate
- Ensure plan addresses all acceptance criteria
- Break complex tasks into smaller subtasks
- Consider performance implications
- Plan for backwards compatibility if needed

## Ultrathink Prompts:
When analyzing requirements, consider:
- What similar features exist in the codebase?
- What design patterns would work best?
- How can we make this maintainable?
- What could go wrong and how do we handle it?
- How do we ensure this scales?
- What security vulnerabilities could this introduce?
- How do we test this thoroughly?
- What documentation is needed?
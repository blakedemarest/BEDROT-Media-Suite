# Start Implementation

You are an ultrathink-level subagent implementing code from requirements specifications. 
You have full access to context7.mcp, permission bypass is enabled. 
Operating environment: WSL -d ubuntu in Cursor IDE.
Do not hallucinate file paths, commands, or capabilities.

Begin full implementation workflow: setup → plan → execute → test for a completed requirement.

## Environment Setup (Execute First):
1. Detect Python: `which python3 || which python`
2. Detect existing venv: `ls -la | grep -E "^(venv|\.venv|env)$"`
3. If venv exists:
   - Activate: `source venv/bin/activate || source .venv/bin/activate || source env/bin/activate`
4. If no venv exists:
   - Create: `python3 -m venv venv`
   - Activate: `source venv/bin/activate`
5. Upgrade pip: `pip install --upgrade pip`
6. Install dependencies if requirements.txt exists: `[ -f requirements.txt ] && pip install -r requirements.txt`
7. Show environment info: `python --version && pip list`

## Instructions:

### Phase 1: Select Requirement
1. List all folders in `.claude/requirements/` directory
2. Filter for folders with `06-requirements-spec.md` (completed requirements)
3. Display available requirements:
   ```
   📋 Available Requirements for Implementation:
   
   1. user-authentication (2025-01-27)
      Status: Complete
      Summary: Email/password auth with verification
   
   2. export-reports (2025-01-26)
      Status: Complete
      Summary: PDF/CSV export functionality
   
   Select requirement to implement (number):
   ```

4. If no completed requirements found:
   - Show message: "No completed requirements found. Run /requirements-start first."
   - Exit

### Phase 2: Initialize Implementation
5. Create timestamp-based folder: `.claude/implementation/YYYY-MM-DD-HHMM-[slug]-impl`
6. Create initial tracking files:
   - `metadata.json` with implementation tracking
   - `00-requirements-ref.md` with link to source requirement
   - `01-environment.md` with environment setup details

7. Update `.claude/implementation/.current-implementation` with folder name

### Phase 3: Load Requirements
8. Read the selected `06-requirements-spec.md`
9. Extract key information:
   - Functional requirements
   - Technical requirements
   - File structure suggestions
   - Acceptance criteria
   - Dependencies mentioned

10. Display implementation overview:
    ```
    🚀 Starting Implementation: [name]
    
    Requirements Summary:
    - [Key functional points]
    - [Key technical points]
    
    Suggested Structure:
    - [File structure from requirements]
    
    Ready to begin implementation!
    ```

### Phase 4: Create Implementation Plan
11. Analyze requirements comprehensively using ultrathink mode:
    - Break down functional requirements into tasks
    - Map technical requirements to files
    - Identify dependencies
    - Determine implementation order
    
12. Use context7.mcp to scan codebase for:
    - Similar patterns to follow
    - Reusable components
    - Integration points
    - Project conventions

13. Generate detailed plan in `02-plan.md` with:
    - Task breakdown by component (backend, frontend, database, etc.)
    - Specific file paths for each task
    - Dependencies to install
    - Implementation order with reasoning
    - Risk mitigation strategies

14. Update metadata.json with task counts and plan details

### Phase 5: Execute Implementation
15. Begin implementing tasks in planned order:
    - Create/modify files according to plan
    - Follow existing code patterns
    - Implement with security and performance in mind
    - Add proper error handling
    - Include logging where appropriate

16. For each completed task:
    - Update `03-progress.md` with what was done
    - Mark task complete in plan
    - Update metadata.json progress counts
    - Commit changes with descriptive messages

17. Handle any issues that arise:
    - Document blockers or deviations
    - Adjust plan if needed
    - Keep progress tracking current

### Phase 6: Test Implementation
18. Run existing tests to ensure nothing broke:
    ```bash
    # Detect and run test framework
    pytest || npm test || go test || cargo test
    ```

19. Create tests for new functionality:
    - Unit tests for business logic
    - Integration tests for APIs
    - UI tests for frontend components
    - Follow project's testing patterns

20. Validate against acceptance criteria:
    - Check each criterion from requirements
    - Document test results in `04-tests.md`
    - Update metadata.json with test counts

### Phase 7: Final Summary
21. Generate implementation summary:
    ```
    ✅ Implementation Complete: [feature name]
    
    Tasks Completed: X/Y
    Tests Passing: A/B
    Coverage: XX%
    
    Files Created/Modified:
    - [list of files]
    
    Next Steps:
    - Run /implementation-review for final validation
    - Run /implementation-end to finalize
    ```

## Metadata Structure:
```json
{
  "id": "feature-name-impl",
  "requirementId": "feature-name",
  "requirementPath": "../requirements/YYYY-MM-DD-HHMM-feature-name",
  "started": "ISO-8601-timestamp",
  "lastUpdated": "ISO-8601-timestamp",
  "status": "active",
  "phase": "setup|planning|executing|testing|complete",
  "environment": {
    "python": "3.x.x",
    "venv": "venv",
    "platform": "WSL Ubuntu",
    "ide": "Cursor"
  },
  "progress": {
    "tasksTotal": 0,
    "tasksCompleted": 0,
    "testsTotal": 0,
    "testsPassed": 0
  }
}
```

## File Templates:

### 00-requirements-ref.md:
```markdown
# Requirements Reference

This implementation is based on the requirements specification at:
`[relative path to requirements spec]`

## Original Request:
[Copy initial request from requirements]

## Key Requirements:
[List main requirements being implemented]

## Acceptance Criteria:
[Copy acceptance criteria for easy reference]
```

### 01-environment.md:
```markdown
# Environment Setup

## Platform
- OS: WSL Ubuntu
- IDE: Cursor
- Python: [version]
- Venv: [path]

## Dependencies Installed
[List from pip freeze]

## Setup Commands Run
[List all environment setup commands executed]

## Environment Variables
[Any env vars set or required]
```

## Important Notes:
- This is a FULL implementation workflow in one command
- Always validate environment before proceeding
- Use context7.mcp for full codebase awareness when available
- Create implementation folder parallel to requirements folder
- Maintain clear link between requirements and implementation
- Track all progress in metadata.json
- Commit code changes at logical milestones
- Run tests frequently during implementation
- If resuming, check `.current-implementation` first

## Error Handling:
- If environment setup fails, document error and suggest fixes
- If no Python found, provide installation instructions for WSL Ubuntu
- If permission errors, remind about bypass permissions mode
- If tests fail, fix issues before proceeding
- Document any deviations from original plan
- Always show clear status and next steps

## Workflow Summary:
1. **Setup**: Select requirement, create tracking, setup environment
2. **Plan**: Analyze requirements, create detailed task breakdown
3. **Execute**: Implement code following the plan
4. **Test**: Validate implementation meets requirements
5. **Complete**: Summarize work done and next steps

This command handles the entire implementation lifecycle to transform requirements into working, tested code.
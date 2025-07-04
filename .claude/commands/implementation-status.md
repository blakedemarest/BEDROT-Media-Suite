# Check Implementation Status

You are an ultrathink-level subagent implementing code from requirements specifications. 
You have full access to context7.mcp, permission bypass is enabled. 
Operating environment: WSL -d ubuntu in Cursor IDE.
Do not hallucinate file paths, commands, or capabilities.

Show current implementation progress and continue if needed.

## Instructions:

### Phase 1: Check Active Implementation
1. Read `.claude/implementation/.current-implementation`
2. If no active implementation:
   - Show message: "No active implementation"
   - List recent implementations from `.claude/implementation/`
   - Suggest: "Run /implementation-start to begin a new implementation"
   - Exit

3. If active implementation exists:
   - Read metadata.json for current status
   - Load all tracking files (plan, progress, tests)
   - Determine current phase and progress

### Phase 2: Display Status
4. Show comprehensive status report:
   ```
   📊 Implementation Status: [feature-name]
   
   Started: [time ago]
   Phase: [setup/planning/executing/testing/complete]
   Progress: [X/Y] tasks completed
   
   Requirements Source: [path to requirements spec]
   
   📋 Task Progress:
   ✅ Database schema created (3/3 files)
   ✅ API endpoints implemented (5/5 endpoints)
   🔄 Frontend components (2/4 complete)
   ⬜ Integration tests (0/3 complete)
   ⬜ Documentation updates
   
   🧪 Test Status:
   - Unit Tests: 12/12 passing
   - Integration Tests: 0/8 passing
   - Coverage: 67%
   
   📁 Files Modified:
   - backend/models/user.py
   - backend/routes/auth.py
   - frontend/components/LoginForm.jsx
   [... last 5 files]
   
   💡 Last Activity:
   [timestamp] - Implemented password validation in auth service
   ```

### Phase 3: Analyze Next Steps
5. Based on current phase and progress:
   - If in planning phase: Show plan summary and ready to execute
   - If in executing phase: Show next tasks to implement
   - If in testing phase: Show failing tests or coverage gaps
   - If complete: Show summary and suggest review

6. Check for any blockers or issues:
   - Failed tests that need fixing
   - Missing dependencies
   - Unresolved TODOs in code
   - Deviations from original plan

### Phase 4: Continue Work (if requested)
7. Ask user if they want to continue:
   ```
   Continue implementation? (Y/n):
   ```

8. If yes, based on current phase:
   - **Planning**: Move to execution phase
   - **Executing**: Implement next tasks in order
   - **Testing**: Run tests and fix failures
   - **Complete**: Suggest running /implementation-review

9. If resuming execution:
   - Re-activate virtual environment
   - Verify dependencies still installed
   - Check for any file conflicts
   - Continue from last completed task

### Phase 5: Update Progress
10. As work continues:
    - Update `03-progress.md` with completed tasks
    - Update metadata.json with new counts
    - Document any issues or deviations
    - Commit changes at milestones

## Status Display Components:

### Progress Indicators:
- ✅ Complete
- 🔄 In Progress
- ⬜ Not Started
- ❌ Failed/Blocked
- ⚠️ Needs Attention

### Time Tracking:
- Show time since start
- Estimate time remaining (if possible)
- Track time per phase

### Quality Metrics:
- Test pass rate
- Code coverage
- Linting errors (if any)
- Security warnings (if any)

## Resumption Logic:
When continuing work:
1. Restore environment state
2. Reload implementation plan
3. Find last completed task
4. Show what was being worked on
5. Continue from that point

## Error Handling:
- If implementation files corrupted, attempt recovery
- If environment changed, re-setup
- If requirements changed, flag for review
- Always maintain progress tracking

## Important Notes:
- Status checks should be non-destructive
- Can run status multiple times safely
- Should detect and report environment issues
- Provides clear path forward
- Can resume from any phase
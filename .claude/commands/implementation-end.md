# End Implementation

You are an ultrathink-level subagent implementing code from requirements specifications. 
You have full access to context7.mcp, permission bypass is enabled. 
Operating environment: WSL -d ubuntu in Cursor IDE.
Do not hallucinate file paths, commands, or capabilities.

Finalize the current implementation session.

## Instructions:

### Phase 1: Check Implementation State
1. Read `.claude/implementation/.current-implementation`
2. If no active implementation:
   - Show "No active implementation to end"
   - Exit

3. Load implementation metadata and review status:
   - Check completion percentage
   - Review test results
   - Check for unfinished tasks

### Phase 2: Present Options
4. Show current status and ask user intent:
   ```
   📊 Implementation Status: [feature-name]
   
   Progress: [X/Y] tasks complete ([percentage]%)
   Tests: [A/B] passing
   Phase: [current phase]
   
   How would you like to finalize this implementation?
   
   1. Complete - Mark as successfully implemented
   2. Partial - Save progress for later continuation  
   3. Archive - Archive with notes (for abandoned work)
   4. Cancel - Delete implementation tracking
   ```

### Phase 3: Process Based on Choice

#### Option 1: Complete Implementation
5. If marking complete:
   - Verify all critical tasks are done
   - Ensure tests are passing
   - Create final summary in `06-summary.md`:
   ```markdown
   # Implementation Summary: [Feature Name]
   
   Completed: [timestamp]
   Duration: [total time]
   
   ## What Was Built
   [Brief description of implemented functionality]
   
   ## Files Created/Modified
   ### New Files:
   - [path/to/new/file1.py] - [purpose]
   - [path/to/new/file2.js] - [purpose]
   
   ### Modified Files:
   - [path/to/modified/file1.py] - [changes made]
   - [path/to/modified/file2.js] - [changes made]
   
   ## Key Achievements
   - ✅ [Achievement 1]
   - ✅ [Achievement 2]
   - ✅ [Achievement 3]
   
   ## Test Results
   - Unit Tests: [X/Y] passing
   - Integration Tests: [A/B] passing
   - Coverage: [percentage]%
   
   ## Dependencies Added
   - [package1] - [purpose]
   - [package2] - [purpose]
   
   ## Deployment Notes
   [Any special deployment considerations]
   
   ## Known Limitations
   [Any limitations or future improvements needed]
   ```

6. Update requirements status:
   - Navigate to linked requirements folder
   - Update requirements metadata.json:
   ```json
   {
     "status": "implemented",
     "implementationDate": "[timestamp]",
     "implementationPath": "[path to implementation]"
   }
   ```

7. Clean up:
   - Clear `.claude/implementation/.current-implementation`
   - Update implementation metadata status to "complete"
   - Archive any temporary files

#### Option 2: Partial Save
8. If saving partial progress:
   - Update metadata status to "paused"
   - Document current state in `99-pause-notes.md`:
   ```markdown
   # Implementation Paused
   
   Paused At: [timestamp]
   Progress: [X/Y] tasks
   
   ## What's Complete
   [List completed components]
   
   ## What's Remaining
   [List pending tasks]
   
   ## Next Steps When Resuming
   1. [Specific next task]
   2. [Following task]
   
   ## Known Issues
   [Any blockers or issues to resolve]
   ```
   
   - Clear `.current-implementation`
   - Show how to resume later

#### Option 3: Archive
9. If archiving:
   - Update metadata status to "archived"
   - Create `99-archive-notes.md`:
   ```markdown
   # Implementation Archived
   
   Archived: [timestamp]
   Reason: [user provided reason]
   
   ## Work Completed
   [What was done before archiving]
   
   ## Why Archived
   [Explanation]
   
   ## Lessons Learned
   [Any insights for future implementations]
   ```
   
   - Clear `.current-implementation`
   - Keep files for reference

#### Option 4: Cancel
10. If canceling:
    - Confirm deletion: "This will delete all implementation tracking. Are you sure? (y/N)"
    - If confirmed:
      - Remove implementation folder
      - Clear `.current-implementation`
      - Show "Implementation tracking deleted"

### Phase 4: Update Index
11. Update `.claude/implementation/index.md`:
    ```markdown
    # Implementation History
    
    ## Active
    [None or current active]
    
    ## Completed
    - ✅ [feature-1] - [date] - [requirements link]
    - ✅ [feature-2] - [date] - [requirements link]
    
    ## Paused
    - ⏸️ [feature-3] - [date] - [progress]
    
    ## Archived
    - 📦 [feature-4] - [date] - [reason]
    ```

### Phase 5: Final Summary
12. Show appropriate final message:
    
    For Complete:
    ```
    ✅ Implementation Finalized: [feature-name]
    
    Total Duration: [time]
    Files Changed: [count]
    Tests Passing: [percentage]%
    
    The implementation has been marked as complete and linked
    to the original requirements.
    
    Next Steps:
    - Deploy the changes
    - Monitor for issues
    - Consider follow-up improvements
    ```
    
    For Partial:
    ```
    ⏸️ Implementation Paused: [feature-name]
    
    Progress Saved: [X/Y] tasks
    
    To resume later, run:
    /implementation-status
    
    Then continue where you left off.
    ```

## Important Notes:
- Always preserve work unless explicitly deleted
- Update all relevant tracking files
- Link implementation to requirements
- Provide clear next steps
- Handle git commits if requested
- Clean up temporary files appropriately
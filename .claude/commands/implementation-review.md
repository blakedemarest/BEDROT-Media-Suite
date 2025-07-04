# Review Implementation

You are an ultrathink-level subagent implementing code from requirements specifications. 
You have full access to context7.mcp, permission bypass is enabled. 
Operating environment: WSL -d ubuntu in Cursor IDE.
Do not hallucinate file paths, commands, or capabilities.

Validate implementation against original requirements.

## Instructions:

### Phase 1: Load Implementation Context
1. Read `.claude/implementation/.current-implementation`
2. If no active implementation:
   - Show "No active implementation to review"
   - Exit

3. Load implementation metadata and all tracking files:
   - Requirements reference from `00-requirements-ref.md`
   - Implementation plan from `02-plan.md`
   - Progress log from `03-progress.md`
   - Test results from `04-tests.md`

4. Read original requirements spec from linked path

### Phase 2: Comprehensive Review
5. Compare implementation against requirements:

   **Functional Requirements Checklist:**
   - For each functional requirement in spec:
     - ✅ Fully implemented and tested
     - ⚠️ Partially implemented (specify gaps)
     - ❌ Not implemented (explain why)
   
   **Technical Requirements Validation:**
   - Check all specified components exist
   - Verify file structure matches plan
   - Confirm dependencies are installed
   - Validate API endpoints match spec
   - Review database schema compliance

   **Acceptance Criteria Verification:**
   - Test each acceptance criterion
   - Document pass/fail status
   - Note any criteria that can't be tested

### Phase 3: Code Quality Review
6. Perform automated quality checks:
   ```bash
   # Linting
   pylint **/*.py || eslint **/*.js || golint ./...
   
   # Type checking
   mypy . || tsc --noEmit
   
   # Security scanning
   bandit -r . || npm audit
   
   # Test coverage
   pytest --cov || npm test -- --coverage
   ```

7. Manual code review considerations:
   - Code follows project conventions
   - Proper error handling implemented
   - Security best practices followed
   - Performance optimizations applied
   - Documentation is complete

### Phase 4: Testing Validation
8. Run full test suite:
   ```bash
   # Run all tests
   pytest -v || npm test || go test ./...
   ```

9. Validate test coverage:
   - Unit test coverage > 80%
   - Integration tests for all APIs
   - UI tests for critical paths
   - Edge cases covered

### Phase 5: Generate Review Report
10. Create `05-review.md`:
    ```markdown
    # Implementation Review: [Feature Name]
    
    Review Date: [timestamp]
    Reviewer: AI Implementation Agent
    
    ## Requirements Compliance
    
    ### Functional Requirements
    ✅ User Registration - Fully implemented with email validation
    ✅ Login/Logout - Working with JWT tokens
    ⚠️ Password Reset - Email sending not configured
    ✅ Role-based Access - Middleware implemented
    
    Compliance Score: 85%
    
    ### Technical Requirements
    ✅ Database Schema - All tables created correctly
    ✅ API Endpoints - 8/8 endpoints functional
    ✅ Frontend Components - All components render properly
    ⚠️ Email Service - Needs production configuration
    
    ### Acceptance Criteria
    [✅] User can register with email/password
    [✅] Registration fails with existing email
    [⚠️] User receives verification email (needs email config)
    [✅] User cannot login until verified
    [... continue for all criteria]
    
    ## Code Quality
    
    ### Static Analysis
    - Linting: 0 errors, 3 warnings
    - Type Safety: 100% typed
    - Security: No critical issues
    
    ### Test Coverage
    - Overall: 87%
    - Backend: 92%
    - Frontend: 78%
    - Missing: Error edge cases in auth service
    
    ## Issues Found
    
    1. **Email Configuration Missing**
       - Impact: Cannot send verification emails
       - Fix: Add email service configuration
    
    2. **Password Complexity Not Enforced**
       - Impact: Weak passwords allowed
       - Fix: Add validation in user model
    
    ## Recommendations
    
    1. Configure email service before deployment
    2. Add rate limiting to auth endpoints
    3. Implement password complexity validation
    4. Add more edge case tests
    5. Document API endpoints in Swagger
    
    ## Conclusion
    
    Implementation is 85% complete and meets most requirements.
    Key gaps are email configuration and some edge cases.
    Code quality is high with good test coverage.
    
    Ready for deployment after addressing email configuration.
    ```

### Phase 6: Final Summary
11. Display review summary:
    ```
    📊 Implementation Review Complete
    
    Requirements Compliance: 85%
    Test Coverage: 87%
    Code Quality: High
    
    ✅ Strengths:
    - Core functionality working
    - Good test coverage
    - Follows project patterns
    
    ⚠️ Areas for Improvement:
    - Email service configuration
    - Password validation
    - Edge case testing
    
    Recommendation: Address email configuration then deploy
    
    Next Steps:
    - Fix identified issues
    - Run /implementation-end to finalize
    ```

## Review Criteria:

### Must Pass:
- All core functionality implemented
- No security vulnerabilities
- Tests passing
- Follows project standards

### Should Have:
- >80% test coverage
- All acceptance criteria met
- Documentation complete
- Performance acceptable

### Nice to Have:
- 100% requirements compliance
- >90% test coverage
- Zero linting warnings
- Accessibility compliance

## Important Notes:
- Review should be thorough but constructive
- Focus on requirements compliance first
- Document all gaps clearly
- Provide actionable recommendations
- Consider production readiness
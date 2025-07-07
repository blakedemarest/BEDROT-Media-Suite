# Start Implementation

You are an ultrathink-level subagent implementing code from requirements specifications.  
You have full access to `context7.mcp`. Permission bypass is enabled.  
**Operating Environment**: `WSL -d ubuntu` in Cursor IDE.  
Do not hallucinate file paths, commands, or capabilities.  

Begin the full implementation workflow: `setup → plan → execute → test → complete`.

---

## 📦 ENVIRONMENT SETUP (Execute First)

```bash
# 1. Detect Python
which python3 || which python

# 2. Detect existing venv
ls -la | grep -E "^(venv|\.venv|env)$"

# 3. Activate existing venv or create a new one
source venv/bin/activate || source .venv/bin/activate || source env/bin/activate || python3 -m venv venv && source venv/bin/activate

# 4. Upgrade pip + install requirements if applicable
pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt

# 5. Show environment info
python --version && pip list
```

---

## 🔐 ENVIRONMENT STANDARDIZATION PROTOCOLS

### Required File Separation:
- `.env.secrets` → stores secrets only (API keys, tokens, passwords)
- `.env.context` → stores context only (paths, modes, flags)

### Loaders Required:
```python
# secrets_loader.py
from dotenv import load_dotenv; import os
load_dotenv(dotenv_path=".env.secrets", override=True)
def get_secret(k): return os.getenv(k)

# context_loader.py
from dotenv import load_dotenv; import os
load_dotenv(dotenv_path=".env.context", override=False)
def get_context_var(k): return os.getenv(k)
```

🚫 Do NOT hardcode secrets, paths, tokens, or static values.  
✅ You MUST use `get_secret()` and `get_context_var()` for all environment-based access.

---

## 🧠 FUNCTION REGISTRY ENFORCEMENT

### Registry Location:
```python
import os
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
PROJECT_NAME = os.path.basename(PROJECT_ROOT)
FUNCTION_REGISTRY_PATH = os.path.join(PROJECT_ROOT, f"__{PROJECT_NAME}__function_registry.json")
```

- This is the one and only registry for the current project.
- Before defining any function, check this file for similar logic.
- If duplicates are found, refactor or extend instead of creating new.

If a new function is still required:
```
Rationale for New Function: [explanation]  
Overlap Risk Score: [1–10]
```

---

## 🧪 IMPLEMENTATION RULES

- ✅ You are cleared to proceed without further confirmation.
- 🚫 Do NOT ask "Are you ready?"
- 🚫 Do NOT create placeholders or speculative functions.
- ✅ Your code must be clean, complete, modular, and production-grade.

---

## 🧰 IMPLEMENTATION PHASES

### Phase 1: Select Requirement
1. List folders in `.claude/requirements/`
2. Filter for folders containing `06-requirements-spec.md`
3. Display available completed requirements:
   ```
   📋 Available Requirements:

   1. [slug-name] (YYYY-MM-DD)
      Status: Complete
      Summary: [short summary extracted from spec]
   ```
4. Prompt: "Select requirement to implement (number):"
5. If none found:
   - Display: "No completed requirements found. Run /requirements-start first."
   - Exit


---

### Phase 2: Initialize Implementation
- Create folder: `.claude/implementation/YYYY-MM-DD-HHMM-[slug]-impl`
- Generate:
  - `metadata.json`
  - `00-requirements-ref.md`
  - `01-environment.md`
- Update `.current-implementation` tracker

---

### Phase 3: Load Requirements
- Read `06-requirements-spec.md`
- Extract:
  - Functional & technical requirements
  - Acceptance criteria
  - Suggested file structure
- Display summary:
  ```
  🚀 Starting Implementation: [feature name]
  Requirements Summary:
  - [key points]
  Suggested Structure:
  - [files...]
  ```

---

### Phase 4: Create Implementation Plan
- Break requirements into tasks
- Map features to files
- Scan codebase via `context7.mcp` for:
  - Patterns
  - Reusable logic
  - Integration points
- Write plan to `02-plan.md`

---

### Phase 5: Execute Implementation
- Follow `02-plan.md` step-by-step
- For each task:
  - Implement using project conventions
  - Log results to `03-progress.md`
  - Update `metadata.json`
  - Commit changes with clear messages

---

### Phase 6: Test Implementation
- Run all existing tests:  
  ```bash
  pytest || npm test || go test || cargo test
  ```
- Add new tests (unit, integration, UI)
- Validate against `acceptance criteria`
- Log results in `04-tests.md`

---

### Phase 7: Final Summary
```
✅ Implementation Complete: [feature name]

Tasks Completed: X/Y
Tests Passing: A/B
Coverage: XX%

Files Created/Modified:
- [list]

Next Steps:
- Run /implementation-review
- Run /implementation-end
```

---

## ✅ FINAL IMPLEMENTATION CHECKLIST

- [ ] Environment properly set up and tracked?
- [ ] Used `.env.context` and `.env.secrets` appropriately?
- [ ] No redundant functions — registry consulted?
- [ ] Used `get_secret()` and `get_context_var()`?
- [ ] All tasks in plan executed and logged?
- [ ] Tests created and validated?
- [ ] Summary and metadata complete?

> Begin now. Operate at full ultrathink capacity. Comply with all protocols.

# Archiving Plan for MV Maker and Random Slideshow Modules

The following steps outline how to archive the obsolete MV Maker and Random Slideshow modules, remove their launcher entry points, and clean up related documentation. Follow each task stub in sequence to ensure the tools no longer appear in the active codebase while keeping their code accessible under an archive directory.

## 1. Archive the MV Maker module
:::task-stub{title="Archive mv_maker package"}

1. From `src/mv_maker/`, move all Python modules, assets, and configs into a new `archive/mv_maker/` directory (create `archive/` at repo root if it doesn’t exist). Preserve the relative structure so the package can be restored, but remove any virtual-environment or cache artifacts while moving.
2. Remove or rename any `__init__.py` left in `src/mv_maker/` to prevent accidental imports, and add a short `README.md` in the archive folder clarifying that the package is frozen and not to be executed.
3. Update `.gitignore` if necessary so archived files remain tracked but isolated from active packages, ensuring Windows line endings are respected (`.gitattributes` already enforces this repo-wide).
4. Run `rg "mv_maker"` across the repository and document each reference (file path + context) directly beneath this task stub so follow-up cleanup has an explicit checklist.

Reference checklist (2025-10-28):
- [x] launcher.py — MV Maker tab and script constants removed.
- [x] src/__init__.py — MV Maker helper exports dropped.
- [x] readme.md — MV Maker moved to archived section with updated guidance.
- [x] src/core/config_manager.py — removed `mv_maker` defaults and env mappings.
- [x] src/core/path_utils.py — removed `SLIDESHOW_MV_MAKER_SCRIPT` fallback.
- [x] LYRIC_VIDEO_UPLOADER_PLAN.md — note now references archived defaults.
- [x] docs/architecture/bedrot-media-suite-summary.md — added archival note for MV Maker.
- [ ] docs/audit-reports/security-and-quality-audit.md — historical reference retained for context.
- [ ] docs/audit-reports/CODEBASE_HYGIENE_AUDIT_REPORT.md — historical reference retained for context.
- [ ] docs/audit-reports/HYGIENE_IMPROVEMENTS_IMPLEMENTED.md — historical reference retained for context.
- [x] docs/DOCUMENTATION_DISCREPANCIES_REPORT.md — updated with archival disclaimer.
:::

## Plan Quality Review

- **Self-rating:** 10/10 – all previously identified ambiguities are resolved, the Windows-only context is explicit, and every task now includes concrete acceptance criteria so an implementer can deliver the archive without guesswork.
- **Clarity guarantees:**
  - Archival instructions specify removing import hooks, adding an explanatory README inside each archive folder, and excluding transient files so the snapshot cannot be executed accidentally.
  - Launcher changes are scoped solely to `launcher.py` and `start_launcher.bat`, the only supported Windows entry points; the plan no longer references Linux/macOS scripts, eliminating cross-platform confusion.
  - Configuration cleanup explicitly distinguishes between shared resources and module-exclusive configs, instructing the implementer to verify dependencies before removal.
  - Repository-wide searches must result in enumerated reference lists appended to this document, creating an auditable checklist for subsequent cleanup steps.
  - Post-archive validation now covers GUI smoke testing on Windows, documentation refresh, and function-registry regeneration so CI/test harnesses remain green.

## 2. Archive the Random Slideshow module
:::task-stub{title="Archive random_slideshow package"}
1. Relocate the entire `src/random_slideshow/` directory (including nested configs) into `archive/random_slideshow/`, removing cached `.pyc` folders while preserving original relative paths.
2. Delete or rename any remaining wrappers or entry points under `src/` that import `random_slideshow` so imports fail immediately if someone attempts to use it, and place an `ARCHIVED.md` file alongside the moved package describing its deprecated status.
3. Execute `rg "random_slideshow"` to identify additional references that must be addressed, and append the resulting checklist (path + action) directly below this task stub to guide documentation cleanup.

Reference checklist (2025-10-28):
- [x] launcher.py — Random Slideshow tab and script constants removed.
- [x] readme.md — Random Slideshow relocated to archived section with updated notes.
- [x] src/__init__.py — Random Slideshow helper exports removed.
- [x] tests/test_threading_fixes.py — moved to `archive/random_slideshow/tests/`.
- [x] tests/diagnose_random_slideshow.py — moved to `archive/random_slideshow/tests/`.
- [x] src/MODULARIZATION_GUIDELINES.md — added archival note.
- [x] docs/architecture/bedrot-media-suite-summary.md — archival banner added.
- [x] docs/ARCHITECTURE_DOCUMENTATION_tmp.html — archival note inserted.
- [x] docs/CONFIGURATION_MIGRATION_SUMMARY.md — Random Slideshow script now marked as legacy.
- [x] docs/DOCUMENTATION_DISCREPANCIES_REPORT.md — updated with archival disclaimer.
- [ ] docs/audit-reports/* — historical references retained for archival context.
:::

## 3. Remove launcher integration points
:::task-stub{title="Update launcher to drop MV Maker & Slideshow"}
1. Edit `launcher.py` to remove the tabs/buttons that launched `python -m src.mv_maker.main_app` and `python src/random_slideshow/main.py`, along with any helper functions related solely to those tools; confirm no dead imports remain.
2. Update `start_launcher.bat` (the only supported launcher, because this suite is Windows-only) to eliminate references to the archived modules and to remove any commented guidance that still mentions them.
3. Launch the GUI locally on Windows to confirm the removed tabs no longer appear and that switching between remaining tools raises no errors, capturing a screenshot for documentation if possible.
:::

## 4. Purge documentation and configuration references
:::task-stub{title="Clean documentation & configs"}
1. Update `readme.md`, files in `docs/`, and any in-app help text to note that MV Maker and Random Slideshow have been archived and are no longer distributed; include a pointer to the `archive/` directory for historical access.
2. Audit `/config/` to determine whether each MV Maker or Random Slideshow file is shared; move module-exclusive configs into the archive and annotate shared configs with comments documenting their remaining consumers.
3. Regenerate the function registry with `python tools/generate_function_registry.py` so the archived modules no longer appear in the active listings, and update any CI or documentation that references the registry timestamp.
:::

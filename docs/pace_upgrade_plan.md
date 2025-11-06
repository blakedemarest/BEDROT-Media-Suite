# PACE Brief: Elevating Context Infrastructure to 10/10

## Problem
Agents inherit a partially unified ecosystem: configs live in multiple directories, scripts rely on manual validation, launch paths drift between legacy and modular versions, and context aids like the function registry demand manual upkeep. These gaps slow onboarding, force guesswork, and increase the risk of hallucinated behavior or stale assumptions.

## Action
1. **Standardize configuration access.** Migrate every tool to the shared `src/core/config_manager.py`, remove duplicate loaders, and consolidate canonical presets under `config/`.
2. **Harden automated testing and CI.** Replace print-driven diagnostics with pytest modules, expand coverage for config and launcher flows, and wire the suite into a minimal GitHub Actions workflow.
3. **Reduce entry-point and legacy drift.** Authoritative documentation should map each user-facing tool to its supported launcher, while deprecated scripts emit guidance or forward to modular implementations.
4. **Automate context artifacts.** Ensure the function registry regenerates automatically after merges and maintain changelog notes for shared utilities inside `CLAUDE.md`.

## Context
* **Existing materials.** Review `CLAUDE.md`, the root `AGENTS.md`, and `bedrot_media_suite_function_registry.json` for current expectations and entry-point mappings.
* **Configuration sprawl.** Identify module-level config managers in `src/snippet_remixer/`, `src/release_calendar/`, `src/reel_tracker/`, and legacy config directories under `archive/` to plan migrations toward the core manager.
* **Testing landscape.** Inspect scripts in `tests/` to convert them into pytest cases; note any OS-specific assumptions that must be preserved during the rewrite.
* **Automation hooks.** Check `tools/generate_function_registry.py` for inputs/outputs, and inspect `.github/` (create if absent) for integrating CI.

## Expectations
* Deliver a single source of truth for configuration reads, backed by regression tests that exercise defaults and environment overrides.
* Provide a `pytest` command that agents can run locally and via CI, with clear pass/fail output.
* Publish updated documentation that removes ambiguity around launch paths, including inline deprecation notices for legacy scripts.
* Set up automated regeneration (or at minimum, a required CI check) for the function registry and log impactful updates within `CLAUDE.md`.
* After implementation, update onboarding docs to reference the new workflows so future agents can land, validate, and ship changes without chasing context across the repo.

# Archiving Plan for MV Maker and Random Slideshow Modules

The following steps outline how to archive the obsolete MV Maker and Random Slideshow modules, remove their launcher entry points, and clean up related documentation. Follow each task stub in sequence to ensure the tools no longer appear in the active codebase while keeping their code accessible under an archive directory.

## 1. Archive the MV Maker module
:::task-stub{title="Archive mv_maker package"}
1. From `src/mv_maker/`, move all Python modules, assets, and configs into a new `archive/mv_maker/` directory (create `archive/` at repo root if it doesn’t exist). Preserve the relative structure so the package can be restored.
2. Remove or rename any `__init__.py` left in `src/mv_maker/` to prevent accidental imports.
3. Update `.gitignore` if necessary so archived files remain tracked but isolated from active packages.
4. Run `rg "mv_maker"` across the repository and note any references that will require cleanup or documentation updates.
:::

## 2. Archive the Random Slideshow module
:::task-stub{title="Archive random_slideshow package"}
1. Relocate the entire `src/random_slideshow/` directory (including nested configs) into `archive/random_slideshow/`.
2. Delete or rename any remaining wrappers or entry points under `src/` that import `random_slideshow` so imports fail immediately if someone attempts to use it.
3. Execute `rg "random_slideshow"` to identify additional references that must be addressed or documented.
:::

## 3. Remove launcher integration points
:::task-stub{title="Update launcher to drop MV Maker & Slideshow"}
1. Edit `launcher.py` to remove the tabs/buttons that launched `python -m src.mv_maker.main_app` and `python src/random_slideshow/main.py`, along with any helper functions related solely to those tools.
2. Update `start_launcher.bat` (and any other platform-specific launch scripts) to eliminate references to the archived modules.
3. Launch the GUI locally to confirm the removed tabs no longer appear and that switching between remaining tools raises no errors.
:::

## 4. Purge documentation and configuration references
:::task-stub{title="Clean documentation & configs"}
1. Update `readme.md`, files in `docs/`, and any in-app help text to note that MV Maker and Random Slideshow have been archived and are no longer distributed.
2. Remove their configuration files from `/config/` if they are no longer required, or clearly mark them as archived copies alongside the relocated code.
3. Regenerate the function registry with `python tools/generate_function_registry.py` so the archived modules no longer appear in the active listings.
:::

# Preserving Local Data in a Checkout

Git intentionally ignores several local files in Time-Tracker. **Ignored does not mean disposable.** Some ignored files contain personal activity history, saved reports, or settings that may not be recoverable if deleted.

Before cleaning, resetting, or replacing a development checkout, inspect its ignored files and identify which data you need to preserve.

## Personal and Local Data

The repository's `.gitignore` includes the following local data paths:

- **`data/`** — local activity data and history.
- **SQLite databases and sidecars** — files matching `*.db`, `*.db-shm`, `*.db-wal`, `*.sqlite`, and `*.sqlite3`. Database files and their sidecars may be important to the same local database.
- **`reports/`** — generated HTML reports that may contain activity details and window titles.
- **`config.json`** — personal application categorization settings.
- **`preferences.json`** — saved application preferences.

Do not assume these files can be regenerated. If you need them, preserve them using the project's existing backup guidance before replacing or cleaning a checkout.

The README's [Reports and data section](../README.md#reports-and-data) explains the SQLite snapshot feature and its limitations. A database snapshot does not include generated HTML reports or `config.json`; preserve those separately when needed.

## Replaceable Environment and Generated Files

The `.gitignore` also excludes development environments and generated files, including:

- `.venv/` and `venv/` — Python virtual environments that can generally be recreated.
- `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, and `.mypy_cache/` — Python bytecode and tool caches.
- `build/`, `dist/`, `release/`, and `*.spec` — build and packaging-related files.

These are generally replaceable, but confirm that any required local changes or build artifacts are not needed before removing them.

## Inspect Ignored Files Safely

From the repository root, run:

```bash
git status --ignored --short
```

This displays the working-tree status, including ignored paths. It does not delete or modify files.

For a particular path, inspect the rule that matches it:

```bash
git check-ignore -v -- data/activity.db
```

Use an actual relative path from your checkout when inspecting a file. The command helps identify the matching ignore rule; it does not establish whether the file is safe to delete.

For example, a fictional checkout might contain:

```text
!! data/
!! reports/
!! config.json
!! preferences.json
!! .venv/
!! __pycache__/
```

The `!!` status indicates ignored paths. A directory may be shown as a whole rather than listing every file beneath it.

Inspect the relevant files and identify what must be retained before making cleanup decisions. If you need to verify the commands, use a disposable clone with harmless marker files rather than personal activity data.

## Before Cleaning a Checkout

1. Inspect ignored files and understand which rules apply.
2. Identify local history, databases and sidecars, reports, and settings that must be retained.
3. Consult the [README backup guidance](../README.md#reports-and-data) and preserve reports and configuration separately from a database snapshot.
4. Verify that any proposed cleanup affects only files you are willing to replace.

**Remember:** Git's ignore rules control what Git normally tracks. They do not provide a backup, guarantee recoverability, or determine whether local data is safe to delete.

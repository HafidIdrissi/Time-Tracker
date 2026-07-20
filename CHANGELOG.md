# Changelog

All notable changes to this project are documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-20

### Changed

- translated the entire desktop interface, reports, installer, command-line
  tools, categories, build messages, and documentation into English;
- renamed the source launcher to `Launch Time Tracker.cmd`;
- made GitHub release publication idempotent by replacing assets when a release
  already exists for the tag.

## [1.0.0] - 2026-07-20

### Added

- local foreground-window activity tracking for Windows;
- configurable keyboard and mouse idle detection;
- desktop interface with live activity;
- analysis for today and the last seven days;
- rankings by category, application, and browser tab;
- local SQLite storage and standalone HTML reports;
- Start, Stop, Reset, reports-folder, and data-management controls;
- PyInstaller executable and distributable Inno Setup installer;
- automated tests and tag-triggered GitHub release workflow;
- MIT License, privacy policy, legal notice, and signing guidance.

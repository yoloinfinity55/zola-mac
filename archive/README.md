# Zola-Mac Archive

This directory contains files that were part of the development and testing phases of the Zola-Mac project but are not needed for the core rebuilt site.

## Archive Structure

### `development/`
Legacy development files and research documents:
- `.generated_manifest.json` - Old manifest file
- `tts_auto.py`, `txt_to_mp3.py` - Early TTS experimentation scripts
- `input.txt` - Test input file
- `TTS study.md` - Research document on TTS methods

### `audio_tests/`
Audio test files used during development:
- `andrew_test.mp3`, `emma_test.mp3` - Voice test samples
- `web_audio.mp3` - Web content audio test

### `temp_files/`
Temporary and intermediate files:
- `audio_output/` - Processing output directory with chunks and metadata
- `web_audio.*` - Various web content test files
- `index.html.backup2` - Template backup

### `scripts/archive/v1/`
Original monolithic scripts (before modular refactoring):
- `web_to_audio_zola.py` - Original web processing script
- `generate_posts.py` - Original YouTube processing script
- Various experimental and duplicate scripts
- Utility scripts that were consolidated

## Purpose

These files are preserved for:
- **Historical Reference**: Understanding the project's evolution
- **Backup**: In case legacy functionality needs to be restored
- **Research**: TTS and processing method research

## When to Use Archived Files

- **Debugging**: If issues arise that might be related to old functionality
- **Feature Recovery**: If legacy features need to be reimplemented
- **Research**: For understanding alternative approaches that were tried

## Current Active Structure

The active, modular codebase is in:
- `scripts/core/` - Main entry points
- `scripts/processors/` - Modular processing components
- `scripts/generators/`, `scripts/utils/`, `scripts/maintenance/` - Ready for expansion

## Migration Notes

The archived files represent the "before" state - monolithic scripts with mixed concerns. The current structure represents the "after" state - modular, maintainable, and extensible.

**Migration Date**: November 7, 2025
**Migration Reason**: Improve maintainability and scalability through modular architecture

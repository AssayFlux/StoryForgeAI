# Development guide

## Scope discipline

Development follows the roadmap in the master project brief. Complete and test one task before starting the next. Do not mark a feature implemented based on a design or placeholder.

## Local tests

The foundation uses the Python standard library test runner and has no runtime dependencies.

```sh
python -m unittest discover -s tests -v
```

If the optional development extra is installed, pytest can also discover the tests:

```sh
python -m pip install -e ".[dev]"
python -m pytest
```

## Code expectations

- Keep modules small and responsibilities explicit.
- Validate external input at module boundaries.
- Handle missing optional dependencies and model files with actionable errors.
- Never overwrite project data without explicit confirmation.
- Avoid network access during local generation.
- Add regression tests for bug fixes.
- Document platform-specific behavior and distinguish tested platforms.
- Keep dependencies minimal and verify Android/ARM64 support before adoption.

## Git workflow

Use focused commits with descriptive messages. Review the diff before committing. Do not commit downloaded models, generated videos, personal project data, virtual environments, or secrets.

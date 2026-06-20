---
name: python-uv-workflow
description: Standardizes Python operations using the uv package manager for speed and reliability.
---

## General Python Execution
- **Always** use `uv run` instead of `python` or `python3` to execute code.
- Use `uv run -c "..."` for quick one-liners.
- If an operation requires a specific tool (like Ruff or Black), use `uvx <tool>` to run it in a temporary, isolated environment.

## Python project management
- Always use uv add and uv remove to manage dependencies
- Never manually activate or manage virtual environments, use uv run for all commands
- Use [dependency-groups] for dev/test/docs dependencies, not [project.optional-dependencies]
- Use `uv add <package>` for production and `uv add --dev <package>` for development dependencies (like `pytest`)
- Do not manually manage virtualenvs; let `uv` handle the `.venv` directory automatically
- Run tests with `uv run pytest` to ensure the correct environment is used.

## Script Workflow (PEP 723)
When creating standalone Python scripts, follow this workflow:
1. **Initialize**: Use `uv init --script <script_name>.py` to create a script with proper metadata.
2. **Dependencies**: Add dependencies directly to the script file using `uv add --script <script_name>.py <package>`.
3. **Execution**: Run the script with `uv run <script_name>.py`.
4. **Metadata**: Ensure the script header uses the [PEP 723 inline metadata format](https://python.org) (e.g., `# /// script`).


## Sandboxing & Cache
- If working in a restricted environment, set the `UV_CACHE_DIR` environment variable to a writable temporary directory to avoid permission errors.

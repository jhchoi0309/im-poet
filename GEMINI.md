# Repository guidance

For a bare repository URL followed by an installation request, follow [docs/agent-install.md](docs/agent-install.md). Install only im-poet for the current host. For this host use `python3 scripts/install_for_agent.py --host gemini`, or `py -3` on Windows. Add `--project` only when requested. Updates preserve the previous folder by default; pass `--no-backup` when the user explicitly requests replacement without a retained backup. Verify version and package bytes, then check native discovery separately when available.

Version 0.8.1 tracks ideas, examples and objections throughout a full rewrite. It checks the force of claims separately from the style of sentence endings and reads conclusions in the context of each manuscript. Gemini CLI can discover a shared alias; verify the selected path. Gemini Apps uses the [account installation guide](docs/gemini-app.md). Follow [AGENTS.md](AGENTS.md) for development.

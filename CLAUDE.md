# Repository guidance

For a bare repository URL followed by an installation request, follow [docs/agent-install.md](docs/agent-install.md). Install only im-poet for the current host. For this host use `python3 scripts/install_for_agent.py --host claude`, or `py -3` on Windows. Add `--project` only when requested. Updates preserve the previous folder by default; pass `--no-backup` when the user explicitly requests replacement without a retained backup. Verify version and package bytes, then check native discovery separately when available.

Version 0.8.0 adds research-scoped editorial decisions, viewpoint and discourse checks, and independent quality criteria. Its findings are not a universal literary-quality guarantee. Follow [AGENTS.md](AGENTS.md) for development. Local CLI, cloud account skills and Gemini Apps are separate installation surfaces. Higher-priority host and user instructions prevail.

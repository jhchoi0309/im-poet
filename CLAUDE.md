# Repository guidance

A repository link supplies the source when the user asks to install im-poet in the same message or an earlier turn. In Claude Code, run `python3 scripts/install_for_agent.py --host claude`, using `py -3` on Windows. Add `--project` when the user requests project scope. An update keeps the previous folder by default. Use `--no-backup` when the user asks to replace it without keeping a copy. Report the version and path after verifying the files against the source, then check whether Claude Code can find the skill. [Installation guide](docs/agent-install.md)

Read the source and the rewrite in both directions. Check that examples and objections still carry their weight, and that a change in sentence endings leaves each claim as certain as the source makes it. Keep file access and external actions within the user's editing request. [Development guidance](AGENTS.md), [Claude Code checks](docs/compatibility.md)

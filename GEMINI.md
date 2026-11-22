# Repository guidance

When a user shares the repository link and asks for installation, install im-poet for the current host. Run `python3 scripts/install_for_agent.py --host gemini`, using `py -3` on Windows. Add `--project` when the user requests project scope. An update keeps the previous folder by default. Use `--no-backup` when the user asks to replace it without keeping a copy. Compare the version and installed files with the source, then check the path Gemini CLI actually discovers. [Installation guide](docs/agent-install.md)

Read the source and the rewrite in both directions. A new rhythm still needs room for the original examples, objections and uncertainty. For a CLI install, check whether an existing `.agents/skills/im-poet` takes precedence. Install in Gemini Apps through the account's Skills interface. [Gemini app guide](docs/gemini-app.md), [development guidance](AGENTS.md)

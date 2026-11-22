# Repository guidance

A repository link supplies the source when the user asks to install im-poet in the same message or an earlier turn. In Gemini CLI, run `python3 scripts/install_for_agent.py --host gemini`, using `py -3` on Windows. Add `--project` when the user requests project scope. An update keeps the previous folder by default. Use `--no-backup` when the user asks to replace it without keeping a copy. Report the version and path after verifying the files against the source, then check which path Gemini CLI discovers. [Installation guide](docs/agent-install.md)

Read the source and the rewrite in both directions. A new rhythm still needs room for the original examples, objections and uncertainty. For a CLI install, check whether an existing `.agents/skills/im-poet` takes precedence. Install in Gemini Apps through the account's Skills interface. [Gemini app guide](docs/gemini-app.md), [development guidance](AGENTS.md)

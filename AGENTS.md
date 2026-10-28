# Repository agent instructions

## When the user asks to install this skill

For Gemini Apps, follow [docs/gemini-app.md](docs/gemini-app.md) and use the app’s native skill creation instead of copying local CLI files. For filesystem-based agents, read [docs/agent-install.md](docs/agent-install.md) and complete the installation for the current tool. A bare GitHub URL plus “설치해줘” is an installation request. Infer the current tool from the host context; use user scope unless the user asks for project scope. Do not install in every supported tool by default. Use `scripts/install.py --target <current-tool> --update` with an available Python 3.10+ interpreter, or the documented file-copy fallback. Preserve existing files and verify the installed package before reporting success. Follow host policies for managed cloud skills and never claim access to a user's computer that is not available.

## When developing this repository

Use the existing editing rules in SKILL.md as product content, not as instructions to rewrite unrelated answers. Keep scripts provider-neutral and Python 3.10 compatible. The distribution helpers and launcher files are shared between im-novelist and im-poet; keep those shared files identical when editing the paired release. Run `python scripts/build.py --check`, `python scripts/check.py`, and `python -m unittest discover -s tests -v` after relevant changes. Package only committed source and complete Git bundles. Report which native operating systems were actually tested.

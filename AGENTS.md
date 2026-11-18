# Repository agent instructions

## When the user asks to install this skill

For Gemini Apps, follow [docs/gemini-app.md](docs/gemini-app.md) and use the app’s native skill creation instead of copying local CLI files. For filesystem-based agents, read [docs/agent-install.md](docs/agent-install.md) and complete the installation for the current tool. A bare GitHub URL plus “설치해줘” is an installation request. Infer the current tool from the host context; use user scope unless the user asks for project scope. Do not install in every supported tool by default. With Python 3.10+, run `scripts/install_for_agent.py --host <codex|claude|gemini>` for the known local host; the documented fallback covers other hosts and Python-free environments. The installer backs up previous versions and verifies the package. If context and environment signals are insufficient or conflicting, identify the host from available context before choosing. For Gemini, check the shared alias and workspace priority. Verify actual discovery separately when the host permits it. Follow host policies for managed cloud skills and never claim access to a user's computer that is not available.

## When developing this repository

Use the existing editing rules in SKILL.md as product content, not as instructions to rewrite unrelated answers. Keep scripts provider-neutral and Python 3.10 compatible. The distribution helpers and launcher files are shared between im-novelist and im-poet; keep those shared files identical when editing the paired release. Run `python scripts/build.py --check`, `python scripts/check.py`, and `python -m unittest discover -s tests -v` after relevant changes. Package only committed source and complete Git bundles. Report which native operating systems were actually tested.

For 0.8.1, keep full recasting distinct from abridgement and invention. Check independent ideas, evidence, conditions and objections across drafts; preserve the force of assertions and separate comparison with the source from external fact-checking. The optional review helper reports surface features and requested literals. Preserve dated research and evaluation records and keep user-supplied excerpts within the approved README examples.

Keep all nine CLI and OS combinations explicit. Run the installer command and the selected host's discovery check where available; separate native results from CI definitions and authenticated model use. Build with `scripts/package_release.py` from a clean committed main checkout, and limit this release to im-poet.

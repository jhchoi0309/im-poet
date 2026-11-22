# Repository agent instructions

## When the user asks to install this skill

Use this repository link as the source when the user requests installation in the same message or an earlier turn. Read [docs/agent-install.md](docs/agent-install.md) and install im-poet for the current tool. Identify the host from the active environment, resolve conflicting signals before selecting a target, and use user scope unless the user requests project scope. With Python 3.10 or later, run `scripts/install_for_agent.py --host <codex|claude|gemini>` for the identified local host. The guide covers Python-free environments and other hosts. The installer verifies the package and keeps a backup by default. For Gemini CLI, check the shared alias and workspace priority. Report the destination and version verified in the actual installation environment. Check discovery separately when possible. Follow the host's account installation procedure for managed skills, including [Gemini Apps](docs/gemini-app.md).

## When developing this repository

Use the existing editing rules in SKILL.md as product content, not as instructions to rewrite unrelated answers. Keep scripts provider-neutral and Python 3.10 compatible. The distribution helpers and launcher files are shared between im-novelist and im-poet; keep those shared files identical when editing the paired release. Run `python scripts/build.py --check`, `python scripts/check.py`, and `python -m unittest discover -s tests -v` after relevant changes. Package only committed source and complete Git bundles. Report which native operating systems were actually tested.

For 0.8.1, keep full recasting distinct from abridgement and invention. Check independent ideas, evidence, conditions and objections across drafts; preserve the force of assertions and separate comparison with the source from external fact-checking. The optional review helper reports surface features and requested literals. Preserve dated research and evaluation records and keep user-supplied excerpts within the approved README examples.

Keep all nine CLI and OS combinations explicit. Run the installer command and the selected host's discovery check where available; separate native results from CI definitions and authenticated model use. Build with `scripts/package_release.py` from a clean committed main checkout, and limit this release to im-poet.

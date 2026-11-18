#!/usr/bin/env python3
"""Check Codex app-server skill discovery without an account or model request."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from build import SKILL_VERSION


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    expected = (project / ".agents/skills/im-poet/SKILL.md").resolve()
    if not expected.is_file():
        parser.error(f"Expected installed skill does not exist: {expected}")
    command = (["cmd.exe", "/d", "/s", "/c", "codex app-server --stdio"]
               if os.name == "nt" else ["codex", "app-server", "--stdio"])
    proc = subprocess.Popen(command, cwd=project, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
    messages: queue.Queue = queue.Queue()
    errors: list[str] = []

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            messages.put(line)
        messages.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def error_reader() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            errors.append(line)
            del errors[:-20]

    threading.Thread(target=error_reader, daemon=True).start()

    def send(message: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()

    def response(request_id: int) -> dict:
        deadline = time.monotonic() + 60
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for Codex response {request_id}")
            try:
                line = messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError(f"Timed out waiting for Codex response {request_id}") from exc
            if line is None:
                raise RuntimeError("Codex app-server exited before responding: " + ''.join(errors)[-1600:])
            message = json.loads(line)
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"Codex returned an error: {message['error']}")
                return message["result"]

    try:
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "impoet-compat-check", "version": SKILL_VERSION}}})
        response(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "skills/list", "params": {"cwds": [str(project)], "forceReload": True}})
        result = response(2)
        for item in result.get("data", []):
            for skill in item.get("skills", []):
                if (skill.get("name") == "im-poet" and skill.get("enabled") is True
                        and Path(skill["path"]).resolve() == expected):
                    print(f"Codex discovered enabled project skill: {expected}")
                    return 0
        raise RuntimeError("Codex did not report the expected enabled project skill")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inject a recorded emulation run into site/run.html.

The run page replays a chain of attack steps from a JSON blob in its
`#run-data` script tag. That blob started life hand-authored: an invented run
id, an invented fidelity score, on a page whose whole argument is "evidence you
can check". This replaces it with the output of a real run.

Producing a recording (in the app repo, not this one):

    python manage.py export_run_recording <run_id> \\
        --out ../website/mayatrail-web-main/recordings/ambersquid.json

Then commit that file here and this step injects it at build time, the same way
build_playbook.py renders the IR playbook.

With no recording present the page keeps its authored walkthrough and is
stamped `recorded: false`, which makes the player label it an illustrative
walkthrough instead of claiming a measured detection rate. That degradation is
deliberate: the page should never be able to present authored data as measured
just because a build step was skipped.

Usage:
    python scripts/build_run.py             # inject, or stamp as illustrative
    python scripts/build_run.py --check     # verify without writing
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "run.html"
RECORDINGS = ROOT / "recordings"

DATA_RE = re.compile(
    r'(<script type="application/json" id="run-data">)(.*?)(</script>)', re.S
)

# Identifier shapes that must never appear in a published recording. Mirrors
# apps/emulations/run_recording.py in the app repo: that builds by allowlist,
# this is the independent check at the publishing boundary. Two repos, two
# chances to catch it.
LEAK_PATTERNS: list[tuple[str, str]] = [
    (r"arn:aws[a-z-]*:[^\s\"']+", "an ARN"),
    (r"\b(?:AKIA|ASIA|AIDA|AROA|AIPA|ANPA|ANVA)[A-Z0-9]{12,}\b", "an AWS key id"),
    (r"\b\d{12}\b", "an AWS account id"),
    (r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "an email address"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "an IP address"),
    (r"\b(?:i-|vpc-|subnet-|sg-|vol-|ami-|eni-)[0-9a-f]{8,}\b", "a resource id"),
]

PLACEHOLDERS = {"<ARN>", "<AWS_KEY_ID>", "<ACCOUNT_ID>", "<EMAIL>", "<IP>", "<RESOURCE_ID>"}

# AWS-managed policy ARNs use the literal "aws" as the account segment and are
# identical in every account, so naming one leaks nothing. Other ARNs stay
# flagged, including arn:aws:s3:::bucket, which has no account but names a
# bucket.
AWS_MANAGED_ARN = re.compile(r"^arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:aws:")


def _is_benign(value: str, label: str) -> bool:
    """
    True when a match is public vocabulary rather than tenant data.

    Mirrors _is_benign in the app repo's run_recording.py. Kept in step
    deliberately: if the two disagree, one of them is wrong and a recording
    either fails to build or ships something it should not.
    """
    if label == "an ARN":
        return bool(AWS_MANAGED_ARN.match(value))
    if label == "an IP address":
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            return False
        # Private, loopback and link-local addresses identify nothing outside
        # their own network. 169.254.169.254 is instance metadata - the same
        # constant everywhere, and unavoidable in a cloud attack walkthrough.
        return not address.is_global
    return False


def find_leaks(text: str) -> list[str]:
    """
    Report identifier shapes in a recording.

    Args:
        text: The serialised recording.

    Returns:
        Descriptions of what was found, empty when clean.
    """
    found: list[str] = []
    for pattern, label in LEAK_PATTERNS:
        for match in re.finditer(pattern, text):
            value = match.group(0)
            if value in PLACEHOLDERS or _is_benign(value, label):
                continue
            found.append(f"{label}: {value[:60]}")
    return found


def load_recording() -> tuple[dict | None, Path | None, list[str]]:
    """
    Load the newest committed recording, if there is one.

    Returns:
        (recording, path, problems). recording is None when none is committed.
    """
    if not RECORDINGS.is_dir():
        return None, None, []

    candidates = sorted(RECORDINGS.glob("*.json"))
    if not candidates:
        return None, None, []
    if len(candidates) > 1:
        # Ambiguity here would silently publish the wrong run.
        names = ", ".join(p.name for p in candidates)
        return None, None, [f"more than one recording in recordings/: {names}"]

    path = candidates[0]
    raw = path.read_text(encoding="utf-8")

    leaks = find_leaks(raw)
    if leaks:
        return None, path, [f"{path.name} contains {leak}" for leak in leaks]

    try:
        recording = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, path, [f"{path.name} is not valid JSON: {exc}"]

    if not isinstance(recording, dict) or not recording.get("chain"):
        return None, path, [f"{path.name} has no chain to replay"]

    recording["recorded"] = True
    return recording, path, []


def build(check_only: bool = False) -> int:
    """Inject the recording, or stamp the page as illustrative."""
    page = PAGE.read_text(encoding="utf-8")
    match = DATA_RE.search(page)
    if not match:
        print(f"error: no #run-data block in {PAGE}", file=sys.stderr)
        return 1

    recording, path, problems = load_recording()
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1

    if recording is None:
        # Keep the authored walkthrough, but make sure it cannot masquerade as
        # a measurement.
        try:
            current = json.loads(match.group(2))
        except json.JSONDecodeError as exc:
            print(f"error: existing run-data is not valid JSON: {exc}", file=sys.stderr)
            return 1
        current["recorded"] = False
        current.pop("fidelity_score", None)
        payload = json.dumps(current, indent=2, sort_keys=True)
        note = "no recording committed - page stamped illustrative"
    else:
        payload = json.dumps(recording, indent=2, sort_keys=True)
        note = f"injected {path.name}"

    leaks = find_leaks(payload)
    if leaks:
        print("error: refusing to write, identifiers present:", file=sys.stderr)
        for leak in leaks[:20]:
            print(f"  {leak}", file=sys.stderr)
        return 1

    body = "\n" + payload + "\n"
    if match.group(2) == body:
        print(f"run.html already up to date ({note})")
        return 0
    if check_only:
        print("error: run.html is stale - run scripts/build_run.py", file=sys.stderr)
        return 1

    page = page[: match.start(2)] + body + page[match.end(2) :]

    # Keep the static console bar honest about which run is on screen.
    run_id = (recording or {}).get("run_id") or json.loads(payload).get("run_id", "")
    actor = (recording or {}).get("threat_actor") or json.loads(payload).get("threat_actor", "")
    if run_id and actor:
        page = re.sub(
            r'(<span>)[^<]*·[^<]*(</span><span class="sep">·</span>\s*<span>region)',
            lambda m: f"{m.group(1)}{run_id} · {actor}{m.group(2)}",
            page,
            count=1,
        )

    PAGE.write_text(page, encoding="utf-8", newline="")
    print(f"run.html updated ({note})")
    return 0


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    return build(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

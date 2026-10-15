# Run recordings

Drop one recorded emulation run here as JSON and `scripts/build_run.py` injects
it into `site/run.html` at build time, replacing the authored walkthrough the
page ships with by default.

Produce one from the app repo:

```bash
python manage.py export_run_recording <run_id> \
    --out ../website/mayatrail-web-main/recordings/ambersquid.json
```

Exactly one `*.json` file may live here. Two would mean the build has to guess
which run to publish, so it refuses instead.

## Before you record

**Record from a dedicated account you are willing to burn.** Never a customer's,
never your production one. The exporter builds its output by allowlist and no
CloudTrail field is copied by value, but resource and role names still leak org
structure through the fields that *are* published.

Both sides check for identifiers independently — the exporter in the app repo,
`build_run.py` here, and CI on every PR. A hit in any of them is a bug, not a
scrub that needs loosening.

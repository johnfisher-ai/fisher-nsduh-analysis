"""Shared paths. Every tool resolves locations from here, so scripts run from any
working directory. Fill in the project-specific constants below.
"""
from pathlib import Path

SITE      = Path(__file__).resolve().parents[1]     # the git repo
WORKSPACE = SITE.parent                             # one level up, outside git
SOURCE    = WORKSPACE / "source"                    # raw material, never committed
DERIVED   = SITE / "tools" / "derived"              # aggregate intermediates, committed
TEMPLATES = SITE / "tools" / "templates"
PUBLIC    = SITE / "public"                         # the only folder that publishes

BASE_URL  = "https://johnfisher-ai.github.io/fisher-nsduh-analysis"

# ---------------------------------------------------------------------------
# Project-specific. Keep raw inputs listed here rather than hard-coded in scripts,
# so one place tells you what the build depends on.
# ---------------------------------------------------------------------------
RAW_INPUTS: list[str] = []          # e.g. ["survey-export.xlsx"]

def require_raw():
    """Raw inputs are not committed. Fail with an explanation, not a stack trace."""
    missing = [f for f in RAW_INPUTS if not (SOURCE / f).exists()]
    if missing:
        raise SystemExit(
            f"Raw inputs not found in {SOURCE}\n  missing: {', '.join(missing)}\n"
            "These are not committed. This step only runs on a machine that holds them.\n"
            "The committed files under tools/derived/ let every later step run without them.")

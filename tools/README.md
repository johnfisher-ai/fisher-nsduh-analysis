# tools

Everything needed to rebuild the site.

```bash
bash tools/build.sh          # rebuild generated pages
bash tools/build.sh --all    # also recompute from raw material
```

**Keep build scripts here, never in `scratch/`.** `scratch/` is throwaway and outside git,
so anything that lives there makes the site unreproducible on any other checkout.

## The two halves

Split the build so stages that need uncommitted raw material write **aggregate**
intermediates into `derived/`, and commit those. Then every page rebuilds on a fresh
checkout, including CI, without the raw material ever being present.

| | Reads | Writes | Committed |
|---|---|---|---|
| `[raw]` stages | `../source/` | `derived/*.json` | the outputs, yes |
| page builders | `derived/`, `templates/` | `public/*.html` | yes |

## Files

- `paths.py` — every location, plus `require_raw()`. Import from here; do not hard-code paths.
- `chart.py` — SVG chart primitives and the validated colour palette.
- `redact_pdf.py` — removes text objects from a PDF and paints the area black. A black
  box alone is not redaction; the text stays underneath.

## Rules that save time later

**Seed anything randomised** and say so in a comment. A bootstrap interval or a
cross-validated estimate changes if the split changes, and if the number is published,
an unseeded rebuild silently contradicts the page.

**Never write identifiers into `derived/`.** It is committed. Report counts, not keys.

**Verify a rebuild reproduces what is deployed** before trusting a refactor: rebuild and
diff against the live files.

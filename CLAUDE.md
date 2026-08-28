# fisher-nsduh-analysis

<!-- Replace this line with one or two sentences: what this project is and what the
     deliverable actually is. Be concrete. "A 40-page HTML guide to X, published to
     GitHub Pages" beats "a documentation project". -->

**Author: John Fisher.** Repo: `johnfisher-ai/fisher-nsduh-analysis`.

---

## Hard rules

- **Never push.** The author pushes with `bash scripts/push_to_github.sh "message"` and reviews
  before publishing. Commit freely; pushing is the author's.
- **Never `git commit --amend`, rebase, or rewrite history.** Always make a new follow-up commit.
  The author pushes out of band, so treat every existing commit as possibly published. Recovery
  without a force push: `git fetch`, `git reset --soft origin/main`, re-commit the delta.
- **No `Co-Authored-By` trailer** on commits.
- **On resume:** `git log --oneline -5` and confirm what is already pushed before changing anything.

<!-- If this repo is PUBLIC, say so here, and note anything that must never be committed. -->

---

## Layout

| Path | What it is |
|---|---|
| `index.html` | Entry point. |
| `scripts/push_to_github.sh` | Commit and push in one command. The author runs this. |
| `.github/workflows/deploy.yml` | Publishes to GitHub Pages on every push to `main`. |

The workspace **above** this repo (`../source/`, `../scratch/`) holds raw material and throwaway
work. It is deliberately outside git. Read from it freely; never commit from it.

<!-- Add rows as the project grows. Mark anything GENERATED so it never gets hand-edited. -->

---

## House style

<!-- Delete what does not apply. These are the rules that took the stats book 205 chapters to
     learn, and they transfer to most written deliverables. -->

- **American English.** If any spelling is deliberately non-standard (a function name, a data
  value, a proper noun), list it here so a later spelling pass does not "fix" it.
- **No prose em-dashes.** Use commas or parentheses.
- **Prose must read human, not AI.** Avoid precious superlatives, aphoristic one-liners, writerly
  meta-flourishes ("doubles as", "earn the right to"), cutesy filler adverbs, and stacked negative
  parallelism ("not X, it's Y"). Keep real idioms. Read the opening and closing paragraphs aloud
  in your head before committing.
- **Say what you actually found.** No claim in prose that has not been checked against real
  output. If a number is quoted, it came from a run, not from a draft.

---

## Build and validate

<!-- Fill in the exact commands. The point is that regenerating is ONE command, so a change is
     never a manual multi-step ritual that gets done differently each time. -->

```
build:     python3 scripts/build.py
validate:  python3 scripts/validate.py
```

**Validation checklist** — extend as the project grows:

```
0 broken local links
no prose em-dashes
no British spellings except the protected list above
every generated file has a source, and no generated file was hand-edited
```

---

## Traps

<!-- Start empty. Add one line every time something costs you more than ten minutes.
     This section is the most valuable part of the file after six months. -->

- _(nothing yet)_

---

## The site

`public/` is the only folder GitHub Pages serves. Everything else in the repo is
reachable through GitHub but is never on the site host. Do not change the workflow to
publish the repo root: that is how source material ends up on a public URL by accident.
After the first deploy, confirm it:

```
curl -s -o /dev/null -w "%{http_code}\n" https://johnfisher-ai.github.io/fisher-nsduh-analysis/CLAUDE.md   # expect 404
```

Pages must be enabled once by hand, with source **GitHub Actions**. See
`.github/PAGES-SETUP.md`. The workflow header records the two failure modes that cost
real time: never use "Re-run jobs" on a Pages workflow, and a wedged deployment blocks
every later one until it is cancelled.

`tools/build.sh` rebuilds generated pages. Keep build scripts in `tools/`, never in
`scratch/`: `scratch/` is throwaway and outside git, so anything that lives there makes
the site unreproducible.

Split the build so that stages needing uncommitted raw material write **aggregate**
intermediates into `tools/derived/`, and commit those. Then every page rebuilds on a
fresh checkout without the raw material ever being present.

## Look and feel

`public/assets/css/site.css` is the design system. Use its classes rather than adding
one-off styles: `.wrap`, `.kicker`, `.lede`, `.figures`, `.cards`, `.card`, `.note`,
`.scroll` + `table.stats`, `.codewrap`, `figure` + `.figbox`.

Charts are inline SVG built in `tools/chart.py`, not image files, so they follow the
reader's light or dark setting. **The palette is validated, not chosen by eye**: the
three series colours pass colorblind-separation and contrast checks against both
surfaces. Re-validate before substituting any colour.

Wide tables and charts scroll inside their own container. The page body must never
scroll horizontally; check at 375px before calling a page done.

Every page carries a full metadata block: canonical, description, Open Graph, Twitter
card, and image dimensions. Social cards are built from `assets/social/` at exactly
1200x627 (LinkedIn and Open Graph) and 1280x640 (the GitHub repo preview). If the card
dimensions change, update `og:image:width` and `og:image:height` in every page.

## Reporting, when the project involves data

- **Every number must come from executed output**, not from a draft or a recollection.
  Quote the run that produced it.
- **Report effect sizes and confidence intervals, not only p-values.**
- **State the n for every analysis**, including how many records survived each join or
  filter. Attrition is a result.
- **Many tests on many outcomes is a multiplicity problem.** Either correct, or say
  plainly that the tests are exploratory.
- **Anything randomised must be seeded**, and the seed recorded. A cross-validated
  estimate or a bootstrap interval changes if the split changes.
- **Cross-check anything important in a second tool.** Reimplementing a result
  independently catches errors that reading the code does not.
- **American English. No prose em-dashes.** Plain declarative sentences.

## If the project involves data about people

Raw data stays in `source/`, never in the repo. Before committing anything derived from
it, check the values, not just the column names. Identifiers hide in places the schema
does not advertise: free-text fields, PDF metadata, file paths, and document properties.
A black box drawn over text in a PDF is not redaction; the text stays underneath and
comes back out with copy-paste. `tools/redact_pdf.py` removes the text objects.

Scan every page of an output file, not just the first, and verify by extracting text
back out afterwards.

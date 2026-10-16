# fisher-nsduh-analysis

**Major Depressive Episode and Substance Use in the United States**, an analysis of the
National Survey on Drug Use and Health (NSDUH), 2022 to 2024.

Three survey years were pooled to give 134,897 respondents with a usable depression
outcome. The analysis reduces seven substance-use and demographic measures with PCA,
finds four groups by k-means, then predicts past-year major depressive episode with
penalized logistic regression and a classification tree, refitting for class imbalance.

**Author: John Fisher.** Repo: `johnfisher-ai/fisher-nsduh-analysis`.

---

## 1. Name this for the subject, never for its origin

This is the sharpest constraint on the project, sharper than in any previous study, because
**both source documents are written for a different audience and setting, and that framing
runs all the way through them**.

Refer to this work only by its subject: major depressive episode, substance use, the survey
years, the methods. Nothing about where, why or for whom the analysis was originally
produced belongs in the README, the About text, the social cards, any page, the notebook,
commit messages, or file names.

The source material carries that framing in volume, in three places you will meet it:

- the analysis PDF's title line, and a `setwd()` call naming both a working directory and a
  local home path
- the plain-English report's title block, plus roughly fifty in-body references: a recurring
  colored callout that appears about a dozen times, dozens of pointers to an external
  reference document, and an entire subsection built around mapping each technique to that
  document
- one source file name

**Neither source document can be published as-is, or lightly edited.** The site's prose must
be written fresh from the substance. The figures are clean R output and can be reused after
renaming.

Before committing, open the report's title block and one of its colored callouts, take the
recurring terms from them, and grep the staged tree for each. The answer should be nothing.
Do not write those terms into this file.

---

## 2. The data is not committed

`../source/` holds three NSDUH public-use files, about 1.1 GB in total: roughly 59,000
respondents and 2,650 variables per year.

**Do not commit them.** Three independent reasons, any one sufficient:

- **Size.** Each file is over 350 MB, well past GitHub's per-file limit, and the repository
  would become unusable.
- **Redundancy.** SAMHSA distributes these files publicly. Linking to the source is more
  useful than a copy that will go stale.
- **They are still individual-level records.** SAMHSA applies disclosure limitation before
  release, so these are far less sensitive than the restricted files, but they remain one
  row per respondent covering substance use, mental health and suicidality. Publishing
  derived aggregates is the right level.

Cite SAMHSA and link to the public-use file page. Note the survey year in any figure, since
NSDUH questionnaires change between years.

---

## 3. The design variables are in the data and the analysis does not use them

This is the most important thing to establish before repeating any number from the existing
work.

NSDUH is a complex multistage probability sample. The public-use files carry the machinery
for handling it: an analysis weight, a variance stratum, and a variance replicate. The
existing analysis selects ten variables and **none of the three is among them**.

That has two different consequences, and conflating them would be a mistake:

**For prediction, it is largely defensible.** The modeling here builds and evaluates a
classifier. Cross-validated AUC on unweighted data answers "how well does this model rank
these respondents", which is a coherent question.

**For describing the population, it is not.** NSDUH deliberately oversamples some groups,
so an unweighted percentage is a property of the sample, not an estimate for the country.
Every prevalence figure in the existing work, the rates by year, and the rates by sex,
income and age, is an unweighted sample percentage. The write-up describes these as facts
about Americans. They are not, until they are weighted.

**Pooling years needs care too.** When NSDUH years are combined, the analysis weight has to
be divided by the number of years, or the pooled estimates imply a population several times
too large. Check whether that was done.

Recommended handling for the site: compute the descriptive figures **both ways**, weighted
and unweighted, and show the difference. That converts a methodological problem into the
most interesting descriptive result the site can offer. Use the `survey` package in R or
`statsmodels`/`samplics` in Python, and always report which is which.

---

## 4. What the analysis does

| Step | Method |
|---|---|
| Clean | Pool three years, select ten variables, recode to binary indicators, listwise deletion |
| Explore | Missingness pattern, prevalence by year, MDE rate by sex, income and age |
| Reduce | PCA on seven standardized variables |
| Group | K-means on the principal component scores, K chosen by elbow plot |
| Predict | LASSO and ridge penalized logistic regression, and a CART classification tree |
| Validate | 10-fold cross-validation, accuracy, kappa, ROC and AUC |
| Refit | Class-weighted models and threshold adjustment for the imbalanced outcome |

Outcome: past-year major depressive episode. Predictors: past-month alcohol, marijuana and
cigarette use, sex, age band, income band, self-rated health.

---

## 5. What it found, and what to check

Reported in the existing work. Verify each against the data before repeating it.

- Four groups: high-income social drinkers, young low-use, older poor-health cigarette
  users, and a polysubstance group described as the public-health priority.
- Self-rated health and age are the strongest predictors of depression; women are at
  higher risk; marijuana is the strongest substance predictor, roughly three and a half
  times alcohol or cigarettes.
- Income adds nothing once the other variables are known, which LASSO found on its own.
- Cross-validated AUC 0.741.
- The outcome is imbalanced at about 7.9 to 1, and at the default threshold kappa is 0:
  the model predicts "no depression" for essentially everyone. The existing work reports
  this openly and refits with class weights and threshold adjustment.

Worth establishing before any of it reaches the site:

- **The weighting question in section 3**, which affects every descriptive claim.
- **Kappa of 0 with 88.7% accuracy is the headline, not a footnote.** A classifier that
  never predicts the minority class is a good illustration of why accuracy alone misleads,
  and the site should lead with it rather than bury it.
- **Cluster interpretation is not a finding.** K-means will return four groups from any
  data. Whether these are real types of people or an artifact of partitioning a continuum
  needs a stability check: refit on resamples and see whether the same structure appears.
- **Listwise deletion dropped about 39,000 records** on the outcome alone. Establish who
  those respondents are. If the depression question was not asked of certain age groups,
  that is a structural gap and should be stated as a restriction on the population, not
  treated as missing data.
- **"Marijuana is 3.5 times alcohol" compares coefficients on binary predictors.** State
  the scale: log-odds, odds ratio, or probability at a stated baseline. A bare ratio of
  coefficients invites misreading.
- Observational data throughout. No causal language.

---

## 6. What this repository should publish

The user has asked specifically for descriptive visuals, methodology and conclusions.

- **Overview** — why depression and substance use are studied together, the data, the four
  groups, and the headline predictive result.
- **The analysis** — descriptives shown weighted against unweighted, PCA and clustering
  with a stability check, the models with cross-validated performance, and the imbalance
  result treated as a finding.
- **The code** — the R pipeline, and a Python notebook. **The notebook cannot embed the
  data**: it is far too large. Either have it download from SAMHSA, or simulate from
  published aggregates, and say which.
- **The write-up** — a plain-language walkthrough, rewritten. The existing report's teaching
  structure is genuinely good and worth keeping; the framing described in section 1 is not.

Figures from the existing report are clean R output and can be reused after renaming, but
prefer regenerating them in the site's own chart style where the data allows, so they
follow the reader's light and dark setting.

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
  - `summarise`, the dplyr function that `R/nsduh_mde_analysis.R` calls, which is also in the
    keyword list in `tools/rhl.py`.
  - `analysed` and `penalised`, keys that `tools/compute_analysis.py` writes into
    `tools/derived/analysis.json`, and the code names built on them (`penalised_rows`,
    `fig_penalised`). Renaming a key means rerunning `bash tools/build.sh --all` on the raw files.
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
three series colors pass colorblind-separation and contrast checks against both
surfaces. Re-validate before substituting any color.

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
- **Anything randomized must be seeded**, and the seed recorded. A cross-validated
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
